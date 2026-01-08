"""
智能合约交互服务

提供与 RAG NFT 合约的交互接口
完全独立，失败时不影响 RAG 功能
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path

from .config import (
    is_web3_available,
    get_rpc_url,
    CHAIN_ID,
    RAG_NFT_CONTRACT,
    RAG_ORACLE_CONTRACT,
    PRIVATE_KEY,
    get_network_config
)

logger = logging.getLogger(__name__)

# 合约 ABI（简化版，完整版在部署后更新）
RAG_NFT_ABI = [
    {
        "inputs": [
            {"name": "question", "type": "string"},
            {"name": "answerHash", "type": "bytes32"},
            {"name": "ipfsCID", "type": "string"}
        ],
        "name": "mintKnowledgeNFT",
        "outputs": [{"name": "tokenId", "type": "uint256"}],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [{"name": "tokenId", "type": "uint256"}],
        "name": "tokenURI",
        "outputs": [{"name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"name": "tokenId", "type": "uint256"}],
        "name": "getAnswerCID",
        "outputs": [{"name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "requestId", "type": "bytes32"},
            {"name": "fullAnswer", "type": "string"}
        ],
        "name": "verify",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "tokenId", "type": "uint256"},
            {"indexed": True, "name": "owner", "type": "address"},
            {"indexed": False, "name": "ipfsCID", "type": "string"}
        ],
        "name": "KnowledgeNFTMinted",
        "type": "event"
    }
]


class ContractService:
    """智能合约交互服务"""
    
    def __init__(self):
        self._web3 = None
        self._nft_contract = None
        self._initialized = False
    
    def _init_web3(self) -> bool:
        """延迟初始化 Web3"""
        if self._initialized:
            return self._web3 is not None
        
        self._initialized = True
        
        if not is_web3_available():
            logger.info("Web3 not enabled, contract service disabled")
            return False
        
        try:
            from web3 import Web3
            
            rpc_url = get_rpc_url()
            if not rpc_url:
                logger.warning("No RPC URL configured")
                return False
            
            self._web3 = Web3(Web3.HTTPProvider(rpc_url))
            
            if not self._web3.is_connected():
                logger.warning(f"Failed to connect to {rpc_url}")
                return False
            
            logger.info(f"Connected to {get_network_config()['name']}")
            
            # 初始化合约
            if RAG_NFT_CONTRACT:
                self._nft_contract = self._web3.eth.contract(
                    address=Web3.to_checksum_address(RAG_NFT_CONTRACT),
                    abi=RAG_NFT_ABI
                )
            
            return True
            
        except ImportError:
            logger.warning("web3 package not installed, contract service disabled")
            return False
        except Exception as e:
            logger.error(f"Web3 initialization error: {e}")
            return False
    
    def is_available(self) -> bool:
        """检查合约服务是否可用"""
        return self._init_web3()
    
    def get_network_info(self) -> Dict[str, Any]:
        """获取当前网络信息"""
        if not self.is_available():
            return {"available": False}
        
        config = get_network_config()
        return {
            "available": True,
            "network": config["name"],
            "chain_id": config["chain_id"],
            "explorer": config["explorer"],
            "nft_contract": RAG_NFT_CONTRACT or "Not deployed",
            "connected": self._web3.is_connected() if self._web3 else False
        }
    
    async def prepare_mint_transaction(
        self,
        user_address: str,
        question: str,
        answer_hash: str,
        ipfs_cid: str
    ) -> Optional[Dict[str, Any]]:
        """
        准备 NFT 铸造交易（供前端签名）
        
        Args:
            user_address: 用户钱包地址
            question: 问题
            answer_hash: 答案哈希
            ipfs_cid: IPFS CID
            
        Returns:
            待签名的交易数据
        """
        if not self.is_available() or not self._nft_contract:
            return None
        
        try:
            from web3 import Web3
            
            # 构建交易
            tx = self._nft_contract.functions.mintKnowledgeNFT(
                question,
                Web3.to_bytes(hexstr=answer_hash),
                ipfs_cid
            ).build_transaction({
                'from': Web3.to_checksum_address(user_address),
                'nonce': self._web3.eth.get_transaction_count(
                    Web3.to_checksum_address(user_address)
                ),
                'gas': 500000,
                'gasPrice': self._web3.eth.gas_price,
                'chainId': CHAIN_ID,
                'value': self._web3.to_wei(0.001, 'ether')  # 铸造费用
            })
            
            return {
                "transaction": tx,
                "estimated_gas": tx['gas'],
                "gas_price_gwei": self._web3.from_wei(tx['gasPrice'], 'gwei'),
                "network": get_network_config()['name']
            }
            
        except Exception as e:
            logger.error(f"Prepare mint transaction error: {e}")
            return None
    
    async def verify_answer(self, request_id: str, full_answer: str) -> Optional[bool]:
        """验证答案是否匹配链上记录"""
        if not self.is_available() or not self._nft_contract:
            return None
        
        try:
            from web3 import Web3
            
            result = self._nft_contract.functions.verify(
                Web3.to_bytes(hexstr=request_id),
                full_answer
            ).call()
            
            return result
            
        except Exception as e:
            logger.error(f"Verify answer error: {e}")
            return None
    
    async def get_token_metadata(self, token_id: int) -> Optional[Dict[str, Any]]:
        """获取 NFT 元数据"""
        if not self.is_available() or not self._nft_contract:
            return None
        
        try:
            token_uri = self._nft_contract.functions.tokenURI(token_id).call()
            answer_cid = self._nft_contract.functions.getAnswerCID(token_id).call()
            
            return {
                "token_id": token_id,
                "token_uri": token_uri,
                "answer_cid": answer_cid,
                "ipfs_url": f"https://gateway.pinata.cloud/ipfs/{answer_cid}"
            }
            
        except Exception as e:
            logger.error(f"Get token metadata error: {e}")
            return None
    
    def generate_mint_params_for_frontend(
        self,
        question: str,
        answer: str,
        ipfs_cid: str
    ) -> Dict[str, Any]:
        """
        生成前端铸造所需的参数（前端直接调用合约）
        
        这个方法不需要后端签名，只是准备数据
        """
        import hashlib
        
        # 生成答案哈希
        answer_hash = hashlib.sha256(answer.encode()).hexdigest()
        
        return {
            "contract_address": RAG_NFT_CONTRACT,
            "chain_id": CHAIN_ID,
            "network": get_network_config()["name"],
            "explorer": get_network_config()["explorer"],
            "function_name": "mintKnowledgeNFT",
            "params": {
                "question": question,
                "answerHash": f"0x{answer_hash}",
                "ipfsCID": ipfs_cid
            },
            "value": "0.001",  # ETH
            "abi": RAG_NFT_ABI
        }


# 单例
_contract_service: Optional[ContractService] = None


def get_contract_service() -> ContractService:
    """获取合约服务实例"""
    global _contract_service
    if _contract_service is None:
        _contract_service = ContractService()
    return _contract_service

