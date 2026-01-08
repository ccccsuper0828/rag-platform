// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title RAGKnowledgeNFT
 * @dev RAG 知识 NFT 合约 - 将 AI 答案铸造为链上 NFT
 * 
 * 功能：
 * 1. 铸造知识 NFT
 * 2. 链上存储内容哈希用于验证
 * 3. IPFS 内容关联
 */
contract RAGKnowledgeNFT is ERC721, ERC721URIStorage, Ownable {
    uint256 private _tokenIds;
    
    // 铸造费用
    uint256 public mintFee = 0.001 ether;
    
    // NFT 内容数据
    struct KnowledgeContent {
        string question;        // 原始问题
        bytes32 answerHash;     // 答案哈希
        string ipfsCID;         // IPFS CID
        uint256 createdAt;      // 创建时间
        address creator;        // 创建者
    }
    
    // tokenId => 内容
    mapping(uint256 => KnowledgeContent) public knowledgeContents;
    
    // 答案哈希 => tokenId (防止重复铸造)
    mapping(bytes32 => uint256) public hashToToken;
    
    // 用户 => 铸造的 token 列表
    mapping(address => uint256[]) public userTokens;
    
    // 事件
    event KnowledgeNFTMinted(
        uint256 indexed tokenId,
        address indexed creator,
        string question,
        bytes32 answerHash,
        string ipfsCID
    );
    
    event MintFeeUpdated(uint256 oldFee, uint256 newFee);
    
    constructor() ERC721("RAG Knowledge NFT", "RAGNFT") Ownable(msg.sender) {}
    
    /**
     * @dev 铸造知识 NFT
     * @param question 问题
     * @param answerHash 答案哈希
     * @param ipfsCID IPFS CID
     */
    function mintKnowledgeNFT(
        string memory question,
        bytes32 answerHash,
        string memory ipfsCID
    ) external payable returns (uint256) {
        require(msg.value >= mintFee, "Insufficient mint fee");
        require(bytes(question).length > 0, "Question cannot be empty");
        require(bytes(ipfsCID).length > 0, "IPFS CID cannot be empty");
        require(hashToToken[answerHash] == 0, "Content already minted");
        
        _tokenIds++;
        uint256 newTokenId = _tokenIds;
        
        // 铸造 NFT
        _safeMint(msg.sender, newTokenId);
        
        // 设置 token URI (指向 IPFS)
        _setTokenURI(newTokenId, string(abi.encodePacked("ipfs://", ipfsCID)));
        
        // 存储内容数据
        knowledgeContents[newTokenId] = KnowledgeContent({
            question: question,
            answerHash: answerHash,
            ipfsCID: ipfsCID,
            createdAt: block.timestamp,
            creator: msg.sender
        });
        
        // 记录哈希映射
        hashToToken[answerHash] = newTokenId;
        
        // 记录用户的 token
        userTokens[msg.sender].push(newTokenId);
        
        // 退还多余的费用
        if (msg.value > mintFee) {
            payable(msg.sender).transfer(msg.value - mintFee);
        }
        
        emit KnowledgeNFTMinted(newTokenId, msg.sender, question, answerHash, ipfsCID);
        
        return newTokenId;
    }
    
    /**
     * @dev 验证答案内容
     */
    function verifyContent(uint256 tokenId, string memory fullAnswer) external view returns (bool) {
        require(ownerOf(tokenId) != address(0), "Token does not exist");
        bytes32 computedHash = keccak256(abi.encodePacked(fullAnswer));
        return knowledgeContents[tokenId].answerHash == computedHash;
    }
    
    /**
     * @dev 获取答案 CID
     */
    function getAnswerCID(uint256 tokenId) external view returns (string memory) {
        require(ownerOf(tokenId) != address(0), "Token does not exist");
        return knowledgeContents[tokenId].ipfsCID;
    }
    
    /**
     * @dev 获取内容详情
     */
    function getContentDetails(uint256 tokenId) external view returns (
        string memory question,
        bytes32 answerHash,
        string memory ipfsCID,
        uint256 createdAt,
        address creator
    ) {
        require(ownerOf(tokenId) != address(0), "Token does not exist");
        KnowledgeContent memory content = knowledgeContents[tokenId];
        return (
            content.question,
            content.answerHash,
            content.ipfsCID,
            content.createdAt,
            content.creator
        );
    }
    
    /**
     * @dev 获取用户铸造的所有 token
     */
    function getUserTokens(address user) external view returns (uint256[] memory) {
        return userTokens[user];
    }
    
    /**
     * @dev 获取总供应量
     */
    function totalSupply() external view returns (uint256) {
        return _tokenIds;
    }
    
    /**
     * @dev 检查哈希是否已铸造
     */
    function isHashMinted(bytes32 answerHash) external view returns (bool) {
        return hashToToken[answerHash] != 0;
    }
    
    /**
     * @dev 更新铸造费用（仅所有者）
     */
    function setMintFee(uint256 newFee) external onlyOwner {
        uint256 oldFee = mintFee;
        mintFee = newFee;
        emit MintFeeUpdated(oldFee, newFee);
    }
    
    /**
     * @dev 提取合约余额（仅所有者）
     */
    function withdraw() external onlyOwner {
        uint256 balance = address(this).balance;
        require(balance > 0, "No balance to withdraw");
        payable(owner()).transfer(balance);
    }
    
    // ==================== 重写必要的函数 ====================
    
    function tokenURI(uint256 tokenId) public view override(ERC721, ERC721URIStorage) returns (string memory) {
        return super.tokenURI(tokenId);
    }
    
    function supportsInterface(bytes4 interfaceId) public view override(ERC721, ERC721URIStorage) returns (bool) {
        return super.supportsInterface(interfaceId);
    }
}
