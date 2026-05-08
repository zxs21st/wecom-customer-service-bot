import re

# 默认分块配置
CHUNK_SIZE = 500      # 每块最大字符数
CHUNK_OVERLAP = 50    # 块之间重叠字符数


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """将文本按语义边界分块"""
    # 先按段落分割
    paragraphs = re.split(r"\n\s*\n", text)

    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue

        # 如果当前块 + 新段落不超过限制，追加
        if len(current_chunk) + len(paragraph) + 1 <= chunk_size:
            current_chunk = current_chunk + "\n\n" + paragraph if current_chunk else paragraph
        else:
            # 保存当前块
            if current_chunk:
                chunks.append(current_chunk)
            # 如果单个段落超过限制，按句子分割
            if len(paragraph) > chunk_size:
                sentences = re.split(r"(?<=[。！？.!?])", paragraph)
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    if len(sentence) > chunk_size:
                        # 强制截断
                        for i in range(0, len(sentence), chunk_size):
                            chunks.append(sentence[i:i + chunk_size])
                    elif len(current_chunk) + len(sentence) + 1 <= chunk_size:
                        current_chunk = current_chunk + " " + sentence if current_chunk else sentence
                    else:
                        chunks.append(current_chunk)
                        current_chunk = sentence
            else:
                current_chunk = paragraph

    if current_chunk:
        chunks.append(current_chunk)

    return chunks
