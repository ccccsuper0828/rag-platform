"""
PDF 转换器：将 PDF 转换为保留格式的文本文件
==============================================

功能：
1. 提取文本并保留段落结构
2. 识别和保留表格（转换为 Markdown 表格格式）
3. 识别图片位置并添加描述占位符
4. 保留页码信息

依赖：
- pdfplumber: 表格和文本提取
- PyMuPDF (fitz): 图片和布局分析
- Pillow: 图片处理（可选，用于 OCR）
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ExtractedImage:
    """提取的图片信息"""
    page_num: int
    image_index: int
    bbox: Tuple[float, float, float, float]  # x0, y0, x1, y1
    width: int
    height: int
    description: str = ""


@dataclass
class ExtractedTable:
    """提取的表格信息"""
    page_num: int
    table_index: int
    headers: List[str]
    rows: List[List[str]]
    bbox: Optional[Tuple[float, float, float, float]] = None


@dataclass
class PageContent:
    """单页内容"""
    page_num: int
    text: str
    tables: List[ExtractedTable]
    images: List[ExtractedImage]
    raw_text_blocks: List[Dict]  # 原始文本块（用于位置合并）


class PDFConverter:
    """
    PDF 转换器：将 PDF 转换为结构化文本
    """
    
    def __init__(self, preserve_tables: bool = True, preserve_images: bool = True):
        """
        初始化转换器
        
        Args:
            preserve_tables: 是否保留表格格式
            preserve_images: 是否标记图片位置
        """
        self.preserve_tables = preserve_tables
        self.preserve_images = preserve_images
    
    def convert(self, pdf_path: str, output_path: Optional[str] = None) -> Tuple[str, str]:
        """
        转换 PDF 到文本文件
        
        Args:
            pdf_path: PDF 文件路径
            output_path: 输出文本文件路径（如果为 None，自动生成）
            
        Returns:
            (output_path, extracted_text): 输出文件路径和提取的文本
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF 文件不存在: {pdf_path}")
        
        if output_path is None:
            output_path = pdf_path.with_suffix('.converted.txt')
        else:
            output_path = Path(output_path)
        
        # 提取内容
        pages = self._extract_all_pages(str(pdf_path))
        
        # 合并为文本
        full_text = self._merge_pages_to_text(pages, pdf_path.name)
        
        # 保存文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_text)
        
        print(f"✅ PDF 已转换为文本: {output_path}")
        print(f"   总页数: {len(pages)}")
        print(f"   文本长度: {len(full_text)} 字符")
        
        return str(output_path), full_text
    
    def extract_text_only(self, pdf_path: str) -> str:
        """
        仅提取文本，不保存文件
        
        Args:
            pdf_path: PDF 文件路径
            
        Returns:
            提取的结构化文本
        """
        pages = self._extract_all_pages(pdf_path)
        return self._merge_pages_to_text(pages, Path(pdf_path).name)
    
    def _extract_all_pages(self, pdf_path: str) -> List[PageContent]:
        """提取所有页面的内容"""
        pages = []
        
        try:
            import pdfplumber
        except ImportError:
            print("⚠️ pdfplumber 未安装，使用 PyMuPDF 基础提取")
            return self._extract_with_pymupdf(pdf_path)
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    page_content = self._extract_page_content(page, i + 1)
                    pages.append(page_content)
        except Exception as e:
            print(f"⚠️ pdfplumber 提取失败: {e}，回退到 PyMuPDF")
            return self._extract_with_pymupdf(pdf_path)
        
        # 使用 PyMuPDF 提取图片信息
        if self.preserve_images:
            self._add_image_info(pdf_path, pages)
        
        return pages
    
    def _extract_page_content(self, page, page_num: int) -> PageContent:
        """使用 pdfplumber 提取单页内容"""
        # 提取表格
        tables = []
        table_bboxes = []
        
        if self.preserve_tables:
            raw_tables = page.extract_tables() or []
            for idx, table_data in enumerate(raw_tables):
                if table_data and len(table_data) > 0:
                    # 清理表格数据
                    cleaned_table = self._clean_table_data(table_data)
                    if cleaned_table:
                        headers = cleaned_table[0] if cleaned_table else []
                        rows = cleaned_table[1:] if len(cleaned_table) > 1 else []
                        tables.append(ExtractedTable(
                            page_num=page_num,
                            table_index=idx,
                            headers=headers,
                            rows=rows
                        ))
            
            # 获取表格边界框
            table_settings = {}
            found_tables = page.find_tables(table_settings)
            for t in found_tables:
                table_bboxes.append(t.bbox)
        
        # 提取文本（排除表格区域）
        text = self._extract_text_excluding_tables(page, table_bboxes)
        
        return PageContent(
            page_num=page_num,
            text=text,
            tables=tables,
            images=[],  # 稍后由 _add_image_info 填充
            raw_text_blocks=[]
        )
    
    def _clean_table_data(self, table_data: List[List]) -> List[List[str]]:
        """清理表格数据"""
        if not table_data:
            return []
        
        cleaned = []
        for row in table_data:
            if row is None:
                continue
            cleaned_row = []
            for cell in row:
                if cell is None:
                    cleaned_row.append("")
                else:
                    # 清理单元格文本
                    cell_text = str(cell).replace('\n', ' ').strip()
                    cleaned_row.append(cell_text)
            
            # 跳过完全空的行
            if any(c for c in cleaned_row):
                cleaned.append(cleaned_row)
        
        return cleaned
    
    def _extract_text_excluding_tables(self, page, table_bboxes: List) -> str:
        """提取文本，排除表格区域"""
        if not table_bboxes:
            return page.extract_text() or ""
        
        # 获取页面上的所有文字
        chars = page.chars
        filtered_chars = []
        
        for char in chars:
            char_x = (char['x0'] + char['x1']) / 2
            char_y = (char['top'] + char['bottom']) / 2
            
            # 检查字符是否在任何表格内
            in_table = False
            for bbox in table_bboxes:
                x0, y0, x1, y1 = bbox
                if x0 <= char_x <= x1 and y0 <= char_y <= y1:
                    in_table = True
                    break
            
            if not in_table:
                filtered_chars.append(char)
        
        # 重建文本
        if not filtered_chars:
            return page.extract_text() or ""
        
        # 按位置排序
        filtered_chars.sort(key=lambda c: (c['top'], c['x0']))
        
        lines = []
        current_line = []
        current_top = None
        line_threshold = 3  # 行间距阈值
        
        for char in filtered_chars:
            if current_top is None:
                current_top = char['top']
            
            if abs(char['top'] - current_top) > line_threshold:
                if current_line:
                    lines.append(''.join(c['text'] for c in current_line))
                current_line = [char]
                current_top = char['top']
            else:
                current_line.append(char)
        
        if current_line:
            lines.append(''.join(c['text'] for c in current_line))
        
        return '\n'.join(lines)
    
    def _add_image_info(self, pdf_path: str, pages: List[PageContent]):
        """使用 PyMuPDF 添加图片信息"""
        try:
            import fitz
        except ImportError:
            print("⚠️ PyMuPDF 未安装，无法提取图片信息")
            return
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_idx, page in enumerate(doc):
                if page_idx >= len(pages):
                    break
                
                image_list = page.get_images()
                
                for img_idx, img_info in enumerate(image_list):
                    xref = img_info[0]
                    
                    try:
                        # 获取图片边界框
                        rects = page.get_image_rects(xref)
                        if rects:
                            rect = rects[0]
                            bbox = (rect.x0, rect.y0, rect.x1, rect.y1)
                            width = int(rect.width)
                            height = int(rect.height)
                        else:
                            bbox = (0, 0, 0, 0)
                            width, height = 0, 0
                        
                        pages[page_idx].images.append(ExtractedImage(
                            page_num=page_idx + 1,
                            image_index=img_idx + 1,
                            bbox=bbox,
                            width=width,
                            height=height,
                            description=f"[图片 {img_idx + 1}：位于第 {page_idx + 1} 页]"
                        ))
                    except Exception as e:
                        print(f"⚠️ 提取图片 {img_idx} 信息失败: {e}")
            
            doc.close()
            
        except Exception as e:
            print(f"⚠️ PyMuPDF 图片提取失败: {e}")
    
    def _extract_with_pymupdf(self, pdf_path: str) -> List[PageContent]:
        """使用 PyMuPDF 进行基础提取"""
        try:
            import fitz
        except ImportError:
            raise ImportError("需要安装 PyMuPDF: pip install PyMuPDF")
        
        pages = []
        doc = fitz.open(pdf_path)
        
        for i in range(doc.page_count):
            page = doc.load_page(i)
            text = page.get_text("text") or ""
            
            # 提取图片
            images = []
            if self.preserve_images:
                image_list = page.get_images()
                for img_idx, img_info in enumerate(image_list):
                    images.append(ExtractedImage(
                        page_num=i + 1,
                        image_index=img_idx + 1,
                        bbox=(0, 0, 0, 0),
                        width=0,
                        height=0,
                        description=f"[图片 {img_idx + 1}]"
                    ))
            
            pages.append(PageContent(
                page_num=i + 1,
                text=text,
                tables=[],  # PyMuPDF 基础模式不提取表格
                images=images,
                raw_text_blocks=[]
            ))
        
        doc.close()
        return pages
    
    def _merge_pages_to_text(self, pages: List[PageContent], filename: str) -> str:
        """合并所有页面为结构化文本"""
        lines = []
        
        # 文件头
        lines.append(f"# {filename}")
        lines.append(f"# 转换时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"# 总页数: {len(pages)}")
        lines.append("")
        lines.append("=" * 60)
        lines.append("")
        
        for page in pages:
            # 页面标题
            lines.append(f"## 【第 {page.page_num} 页】")
            lines.append("")
            
            # 处理文本和表格的混合内容
            content_parts = []
            
            # 添加文本
            if page.text.strip():
                content_parts.append(("text", 0, page.text))
            
            # 添加表格
            for table in page.tables:
                table_md = self._table_to_markdown(table)
                content_parts.append(("table", table.table_index, table_md))
            
            # 添加图片标记
            for img in page.images:
                img_marker = f"\n{img.description}\n"
                content_parts.append(("image", img.image_index, img_marker))
            
            # 按类型组织输出
            for part_type, _, content in content_parts:
                if part_type == "text":
                    lines.append(content)
                elif part_type == "table":
                    lines.append("")
                    lines.append(content)
                    lines.append("")
                elif part_type == "image":
                    lines.append(content)
            
            lines.append("")
            lines.append("-" * 40)
            lines.append("")
        
        return "\n".join(lines)
    
    def _table_to_markdown(self, table: ExtractedTable) -> str:
        """将表格转换为 Markdown 格式"""
        if not table.headers and not table.rows:
            return ""
        
        lines = []
        
        # 表格标题
        lines.append(f"**[表格 {table.table_index + 1}]**")
        lines.append("")
        
        # 确定列数
        if table.headers:
            num_cols = len(table.headers)
        elif table.rows:
            num_cols = max(len(row) for row in table.rows)
        else:
            return ""
        
        # 表头
        if table.headers:
            header_row = "| " + " | ".join(str(h) for h in table.headers) + " |"
            lines.append(header_row)
        else:
            # 使用第一行作为表头
            if table.rows:
                header_row = "| " + " | ".join(str(c) for c in table.rows[0]) + " |"
                lines.append(header_row)
                table.rows = table.rows[1:]
        
        # 分隔线
        separator = "|" + "|".join([" --- " for _ in range(num_cols)]) + "|"
        lines.append(separator)
        
        # 数据行
        for row in table.rows:
            # 确保行有正确的列数
            padded_row = list(row) + [""] * (num_cols - len(row))
            row_str = "| " + " | ".join(str(c) for c in padded_row[:num_cols]) + " |"
            lines.append(row_str)
        
        return "\n".join(lines)


def convert_pdf_after_upload(pdf_path: str, output_dir: Optional[str] = None) -> Tuple[str, str]:
    """
    上传后转换 PDF 的便捷函数
    
    Args:
        pdf_path: PDF 文件路径
        output_dir: 输出目录（如果为 None，使用 PDF 同目录）
        
    Returns:
        (txt_path, extracted_text): TXT 文件路径和提取的文本
    """
    pdf_path = Path(pdf_path)
    
    if output_dir:
        output_path = Path(output_dir) / f"{pdf_path.stem}.txt"
    else:
        output_path = pdf_path.with_suffix('.txt')
    
    converter = PDFConverter(preserve_tables=True, preserve_images=True)
    return converter.convert(str(pdf_path), str(output_path))


# 命令行测试
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python pdf_converter.py <pdf_path> [output_path]")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    txt_path, text = convert_pdf_after_upload(pdf_path, output_path)
    print(f"\n预览 (前 1000 字符):\n{text[:1000]}")

