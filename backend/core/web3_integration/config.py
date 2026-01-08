"""
Web3 配置模块

独立配置，不影响主应用
"""

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# ==================== Web3 配置 ====================
# 启用/禁用 Web3 功能（默认禁用，不影响 RAG）
WEB3_ENABLED = os.getenv("WEB3_ENABLED", "false").lower() == "true"

# 网络配置
NETWORK = os.getenv("WEB3_NETWORK", "sepolia")  # sepolia, mainnet, polygon
RPC_URL = os.getenv("WEB3_RPC_URL", "")
CHAIN_ID = int(os.getenv("WEB3_CHAIN_ID", "11155111"))  # Sepolia

# 合约地址（部署后填写）
RAG_NFT_CONTRACT = os.getenv("RAG_NFT_CONTRACT", "")
RAG_ORACLE_CONTRACT = os.getenv("RAG_ORACLE_CONTRACT", "")

# 私钥（仅用于后端签名，可选）
PRIVATE_KEY = os.getenv("WEB3_PRIVATE_KEY", "")

# ==================== IPFS 配置 ====================
IPFS_ENABLED = os.getenv("IPFS_ENABLED", "false").lower() == "true"
IPFS_API_URL = os.getenv("IPFS_API_URL", "https://api.pinata.cloud")
IPFS_API_KEY = os.getenv("IPFS_API_KEY", "")
IPFS_API_SECRET = os.getenv("IPFS_API_SECRET", "")

# Pinata 配置
PINATA_JWT = os.getenv("PINATA_JWT", "")

# ==================== Arweave 配置（可选永久存储）====================
ARWEAVE_ENABLED = os.getenv("ARWEAVE_ENABLED", "false").lower() == "true"
ARWEAVE_WALLET_PATH = os.getenv("ARWEAVE_WALLET_PATH", "")

# ==================== 网络配置映射 ====================
NETWORK_CONFIG = {
    "sepolia": {
        "rpc_url": os.getenv("SEPOLIA_RPC_URL", "https://sepolia.infura.io/v3/YOUR_KEY"),
        "chain_id": 11155111,
        "explorer": "https://sepolia.etherscan.io",
        "name": "Sepolia Testnet"
    },
    "polygon_amoy": {
        "rpc_url": os.getenv("POLYGON_AMOY_RPC_URL", "https://rpc-amoy.polygon.technology"),
        "chain_id": 80002,
        "explorer": "https://amoy.polygonscan.com",
        "name": "Polygon Amoy Testnet"
    },
    "base_sepolia": {
        "rpc_url": os.getenv("BASE_SEPOLIA_RPC_URL", "https://sepolia.base.org"),
        "chain_id": 84532,
        "explorer": "https://sepolia.basescan.org",
        "name": "Base Sepolia Testnet"
    },
    "mainnet": {
        "rpc_url": os.getenv("MAINNET_RPC_URL", ""),
        "chain_id": 1,
        "explorer": "https://etherscan.io",
        "name": "Ethereum Mainnet"
    }
}


def get_network_config():
    """获取当前网络配置"""
    return NETWORK_CONFIG.get(NETWORK, NETWORK_CONFIG["sepolia"])


def is_web3_available() -> bool:
    """检查 Web3 功能是否可用"""
    if not WEB3_ENABLED:
        return False
    if not RPC_URL and not get_network_config().get("rpc_url"):
        return False
    return True


def get_rpc_url() -> str:
    """获取 RPC URL"""
    return RPC_URL or get_network_config().get("rpc_url", "")

