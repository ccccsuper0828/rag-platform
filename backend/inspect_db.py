import chromadb
from chromadb.config import Settings
import pandas as pd

# 连接到本地持久化的 ChromaDB
# 注意：路径要和 docker-compose 挂载的宿主机路径一致，或者在 backend 目录下运行
# 如果在宿主机运行，路径通常是 ./backend/chroma_db
DB_PATH = "./chroma_db"

print(f"正在连接数据库: {DB_PATH} ...")
try:
    client = chromadb.PersistentClient(path=DB_PATH)
except Exception as e:
    print(f"连接失败: {e}")
    exit()

# 1. 列出所有集合 (Collections)
collections = client.list_collections()
print(f"\n📚 发现 {len(collections)} 个知识库集合:")

if not collections:
    print("   (数据库为空)")
else:
    for i, col in enumerate(collections):
        # 获取集合的统计信息
        count = col.count()
        print(f"   {i+1}. 集合名: {col.name}")
        print(f"      - 数据量: {count} 条片段")
        
        # 2. 窥视前 3 条数据
        peek = col.peek(limit=3)
        if peek and peek['ids']:
            print(f"      - [预览数据]")
            for j in range(len(peek['ids'])):
                doc_id = peek['ids'][j]
                # 尝试获取 metadata
                meta = peek['metadatas'][j] if peek['metadatas'] else {}
                # 截取部分文本
                text = peek['documents'][j] if peek['documents'] else ""
                preview_text = text[:50].replace('\n', ' ') + "..."
                
                print(f"        ID: {doc_id}")
                print(f"        Meta: {meta}")
                print(f"        Text: {preview_text}")
                print("        ---")
        print("\n")

print("✅ 检查完毕。")

