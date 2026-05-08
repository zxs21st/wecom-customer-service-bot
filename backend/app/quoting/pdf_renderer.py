import os
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# PDF 输出目录
PDF_DIR = Path(__file__).parent / "output"
PDF_DIR.mkdir(exist_ok=True)

# 模板目录
TEMPLATE_DIR = Path(__file__).parent / "templates"

try:
    from jinja2 import Environment, FileSystemLoader
    from weasyprint import HTML
    HAS_WEASYPRINT = True
    jinja_env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
except (OSError, ModuleNotFoundError):
    HAS_WEASYPRINT = False
    jinja_env = None
    logger.warning("WeasyPrint not available. PDF generation will use fallback.")


def render_quote_pdf(
    quote_no: str,
    customer_name: str,
    items: list[dict],
    total_amount: float,
    discount_total: float,
    final_amount: float,
    valid_until: str,
    template_name: str = "quote_standard.html",
) -> str:
    """将报价数据渲染为 PDF 文件，返回文件路径"""
    pdf_filename = f"{quote_no}.pdf"
    pdf_path = PDF_DIR / pdf_filename

    if not HAS_WEASYPRINT:
        # 开发环境回退：生成纯文本占位文件
        content = f"""报价单 {quote_no}
客户: {customer_name}
合计: ¥{final_amount:.2f}
有效期: {valid_until}
商品明细: {len(items)} 项
"""
        pdf_path.write_text(content, encoding="utf-8")
        logger.info(f"PDF quote generated (text fallback): {pdf_path}")
        return str(pdf_path)

    template = jinja_env.get_template(template_name)
    html_content = template.render(
        quote_no=quote_no,
        customer_name=customer_name,
        items=items,
        total_amount=total_amount,
        discount_total=discount_total,
        final_amount=final_amount,
        valid_until=valid_until,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
    )

    HTML(string=html_content).write_pdf(str(pdf_path))
    logger.info(f"PDF quote generated: {pdf_path}")
    return str(pdf_path)
