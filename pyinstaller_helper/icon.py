"""图标处理：从 .ico 渲染 PNG 预览、图片转 ICO（纯逻辑，Windows 专用）

预览：用 Shell32 提取 .ico 图标并绘制到内存位图，编码为带透明通道的 PNG。
转 ICO：用 GDI+（零第三方依赖）加载 JPG/PNG/BMP 等图片，缩放到 256×256，
编码为 PNG 字节后塞进 22 字节 ICO 壳；同一套 GDI+ 代码也为普通图片
输出任意尺寸 PNG 字节供 tkinter PhotoImage 预览。
失败（文件不存在、非图标文件等）一律返回 None，由调用方降级处理。
"""

import ctypes
import os
import struct
import tempfile
import zlib
from ctypes import wintypes

DI_NORMAL = 0x0003
DIB_RGB_COLORS = 0
BI_RGB = 0


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", ctypes.c_long),
        ("biHeight", ctypes.c_long),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", ctypes.c_long),
        ("biYPelsPerMeter", ctypes.c_long),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", BITMAPINFOHEADER), ("bmiColors", wintypes.DWORD * 3)]


def _render_icon_bgra(ico_path, size):
    """提取 ico 中的图标并绘制为 size×size 位图，返回 BGRA 像素；失败返回 None"""
    shell32 = ctypes.windll.shell32
    gdi32 = ctypes.windll.gdi32
    user32 = ctypes.windll.user32

    # 显式声明原型，避免 64 位下句柄按 32 位整数传参被截断
    shell32.ExtractIconExW.argtypes = [
        wintypes.LPCWSTR,
        ctypes.c_int,
        ctypes.POINTER(wintypes.HICON),
        ctypes.POINTER(wintypes.HICON),
        wintypes.UINT,
    ]
    shell32.ExtractIconExW.restype = wintypes.UINT
    user32.DrawIconEx.argtypes = [
        wintypes.HDC,
        ctypes.c_int,
        ctypes.c_int,
        wintypes.HICON,
        ctypes.c_int,
        ctypes.c_int,
        wintypes.UINT,
        wintypes.HBRUSH,
        wintypes.UINT,
    ]
    user32.DrawIconEx.restype = wintypes.BOOL
    user32.DestroyIcon.argtypes = [wintypes.HICON]
    user32.DestroyIcon.restype = wintypes.BOOL
    gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
    gdi32.CreateCompatibleDC.restype = wintypes.HDC
    gdi32.CreateDIBSection.argtypes = [
        wintypes.HDC,
        ctypes.POINTER(BITMAPINFO),
        wintypes.UINT,
        ctypes.POINTER(ctypes.c_void_p),
        wintypes.HANDLE,
        wintypes.DWORD,
    ]
    gdi32.CreateDIBSection.restype = wintypes.HBITMAP
    gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
    gdi32.SelectObject.restype = wintypes.HGDIOBJ
    gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
    gdi32.DeleteObject.restype = wintypes.BOOL
    gdi32.DeleteDC.argtypes = [wintypes.HDC]
    gdi32.DeleteDC.restype = wintypes.BOOL

    # 提取大图标（small 数组传 None 表示只取大图标）
    h_icon = wintypes.HICON()
    if shell32.ExtractIconExW(ico_path, 0, ctypes.byref(h_icon), None, 1) < 1:
        return None

    bmi = BITMAPINFO()
    bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.bmiHeader.biWidth = size
    bmi.bmiHeader.biHeight = -size  # 负数：自上而下的行序，读取更直观
    bmi.bmiHeader.biPlanes = 1
    bmi.bmiHeader.biBitCount = 32
    bmi.bmiHeader.biCompression = BI_RGB

    hdc = gdi32.CreateCompatibleDC(None)
    if not hdc:
        user32.DestroyIcon(h_icon)
        return None
    try:
        bits = ctypes.c_void_p()
        hbmp = gdi32.CreateDIBSection(
            hdc, ctypes.byref(bmi), DIB_RGB_COLORS, ctypes.byref(bits), None, 0
        )
        if not hbmp or not bits.value:
            return None
        try:
            old = gdi32.SelectObject(hdc, hbmp)
            # 初始内存全零即透明背景，DrawIconEx 会把带 alpha 的图标绘制上去
            if not user32.DrawIconEx(
                hdc, 0, 0, h_icon, size, size, 0, None, DI_NORMAL
            ):
                return None
            gdi32.SelectObject(hdc, old)
            return ctypes.string_at(bits.value, size * size * 4)
        finally:
            gdi32.DeleteObject(hbmp)
    finally:
        gdi32.DeleteDC(hdc)
        user32.DestroyIcon(h_icon)


def _bgra_to_rgba(bgra):
    """交换 BGRA 的 R/B 通道得到 RGBA（PNG 要求的通道顺序）"""
    b, g, r, a = bgra[0::4], bgra[1::4], bgra[2::4], bgra[3::4]
    return bytes(v for quad in zip(r, g, b, a) for v in quad)


def _encode_png(width, height, rgba):
    """把 RGBA 像素编码为 PNG 字节（标准库手写编码，带透明通道）"""

    def chunk(tag, data):
        payload = tag + data
        return (
            struct.pack(">I", len(data))
            + payload
            + struct.pack(">I", zlib.crc32(payload) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)  # 8 位 RGBA
    stride = width * 4
    raw = bytearray()
    for y in range(height):
        raw.append(0)  # 每行滤镜类型：None
        raw += rgba[y * stride : (y + 1) * stride]
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(bytes(raw), 6))
        + chunk(b"IEND", b"")
    )


def icon_to_png(ico_path, size=48):
    """提取 ico 中的图标，渲染为 size×size 的 RGBA PNG 字节；失败返回 None"""
    try:
        bgra = _render_icon_bgra(ico_path, size)
        if not bgra:
            return None
        return _encode_png(size, size, _bgra_to_rgba(bgra))
    except OSError:
        return None


# ---------------------------------------------------------------- GDI+ 图片转 PNG
class _GdiplusStartupInput(ctypes.Structure):
    _fields_ = [
        ("GdiplusVersion", wintypes.DWORD),
        ("DebugEventCallback", ctypes.c_void_p),
        ("SuppressBackgroundThread", wintypes.BOOL),
        ("SuppressExternalCodecs", wintypes.BOOL),
    ]


class _CLSID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", ctypes.c_ubyte * 8),
    ]


# PNG 编码器 CLSID 是固定值 {557CF406-1A04-11D3-9A73-0000F81EF32E}，硬编码免去枚举
_PNG_CLSID = _CLSID(
    0x557CF406, 0x1A04, 0x11D3, (ctypes.c_ubyte * 8)(0x9A, 0x73, 0x00, 0x00, 0xF8, 0x1E, 0xF3, 0x2E)
)
_INTERP_BICUBIC = 7  # InterpolationModeHighQualityBicubic
_PF_PARGB = 0xE200B  # PixelFormat32bppPARGB：带 alpha，绘制不丢失透明通道


def _gdip_to_png(image_path, size):
    """GDI+ 加载常见图片并缩放到 size×size，编码为 PNG 字节；失败返回 None"""
    try:
        gdiplus = ctypes.windll.gdiplus
        token = ctypes.c_size_t()
        si = _GdiplusStartupInput(1, None, False, False)
        if gdiplus.GdiplusStartup(ctypes.byref(token), ctypes.byref(si), None) != 0:
            return None
        try:
            # 加载源图（GDI+ 原生支持 JPG/PNG/BMP/GIF 等）
            gdiplus.GdipCreateBitmapFromFile.argtypes = [
                wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_void_p)
            ]
            gdiplus.GdipCreateBitmapFromFile.restype = ctypes.c_int
            src = ctypes.c_void_p()
            if gdiplus.GdipCreateBitmapFromFile(image_path, ctypes.byref(src)) != 0 or not src.value:
                return None
            try:
                # 目标位图：size×size PARGB
                gdiplus.GdipCreateBitmapFromScan0.argtypes = [
                    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                    ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p),
                ]
                gdiplus.GdipCreateBitmapFromScan0.restype = ctypes.c_int
                dst = ctypes.c_void_p()
                if gdiplus.GdipCreateBitmapFromScan0(
                    size, size, 0, _PF_PARGB, None, ctypes.byref(dst)
                ) != 0 or not dst.value:
                    return None
                try:
                    g = ctypes.c_void_p()
                    gdiplus.GdipGetImageGraphicsContext.argtypes = [
                        ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)
                    ]
                    gdiplus.GdipGetImageGraphicsContext.restype = ctypes.c_int
                    if gdiplus.GdipGetImageGraphicsContext(dst, ctypes.byref(g)) != 0 or not g.value:
                        return None
                    try:
                        gdiplus.GdipSetInterpolationMode.argtypes = [ctypes.c_void_p, ctypes.c_int]
                        gdiplus.GdipSetInterpolationMode(g, _INTERP_BICUBIC)
                        gdiplus.GdipDrawImageRectI.argtypes = [
                            ctypes.c_void_p, ctypes.c_void_p,
                            ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                        ]
                        gdiplus.GdipDrawImageRectI.restype = ctypes.c_int
                        if gdiplus.GdipDrawImageRectI(g, src, 0, 0, size, size) != 0:
                            return None
                    finally:
                        gdiplus.GdipDeleteGraphics(g)
                    # 经临时文件取回 PNG 字节，避开 IStream 的 COM 释放样板
                    gdiplus.GdipSaveImageToFile.argtypes = [
                        ctypes.c_void_p, wintypes.LPCWSTR,
                        ctypes.POINTER(_CLSID), ctypes.c_void_p,
                    ]
                    gdiplus.GdipSaveImageToFile.restype = ctypes.c_int
                    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                    tmp.close()
                    try:
                        if gdiplus.GdipSaveImageToFile(
                            dst, tmp.name, ctypes.byref(_PNG_CLSID), None
                        ) != 0:
                            return None
                        with open(tmp.name, "rb") as f:
                            return f.read()
                    finally:
                        os.unlink(tmp.name)
                finally:
                    gdiplus.GdipDisposeImage(dst)
            finally:
                gdiplus.GdipDisposeImage(src)
        finally:
            gdiplus.GdiplusShutdown(token)
    except OSError:
        return None


def image_to_png(image_path, size=48):
    """把常见图片缩放为 size×size 的 PNG 字节供预览；失败返回 None"""
    return _gdip_to_png(image_path, size)


def image_to_ico(image_path):
    """把 JPG/PNG/BMP 等图片转为含 256×256 图标的 ICO 字节；失败返回 None"""
    png = _gdip_to_png(image_path, 256)
    if not png:
        return None
    # ICO 壳：ICONDIR(6 字节) + ICONDIRENTRY(16 字节)，PNG 数据紧随其后；
    # 宽高填 0 表示 256。现代 Windows 支持 ICO 内嵌 PNG。
    return (
        struct.pack("<HHH", 0, 1, 1)
        + struct.pack("<BBBBHHII", 0, 0, 0, 0, 1, 32, len(png), 22)
        + png
    )


if __name__ == "__main__":
    # 自检：用现有 PNG 编码器造一张 32×32 红色测试图，走完整转换流程
    test_png = os.path.join(tempfile.gettempdir(), "_icon_test_src.png")
    with open(test_png, "wb") as f:
        f.write(_encode_png(32, 32, bytes([255, 0, 0, 255]) * (32 * 32)))
    ico = image_to_ico(test_png)
    assert ico and ico[:6] == struct.pack("<HHH", 0, 1, 1), "ICO 头错误"
    assert len(ico) == 22 + struct.unpack("<I", ico[14:18])[0], "ICO 长度错误"
    preview = image_to_png(test_png, 48)
    assert preview and preview[:8] == b"\x89PNG\r\n\x1a\n", "预览 PNG 错误"
    os.unlink(test_png)
    print("icon.py 自检通过")
