"""
Web3 集成模块

此模块独立于 RAG 核心功能，提供：
1. 智能合约交互
2. NFT 铸造
3. IPFS 存储
4. 链上验证

设计原则：
- 与 RAG 模块完全解耦
- 可选启用（不影响现有功能）
- 失败时优雅降级
"""

from .nft_service import NFTService
from .ipfs_service import IPFSService
from .contract_service import ContractService
from .web3_router import web3_router

__all__ = [
    'NFTService',
    'IPFSService', 
    'ContractService',
    'web3_router'
]

