// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title SparkKnowledgeNFT
 * @dev 光源知识 NFT 合约 - 整合版（已优化，解决 Stack too deep）
 */

/* ========================= Ownable ========================= */
abstract contract Ownable {
    address public owner;
    
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Ownable: not owner");
        _;
    }
    
    constructor() {
        owner = msg.sender;
        emit OwnershipTransferred(address(0), msg.sender);
    }
    
    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "Ownable: zero addr");
        emit OwnershipTransferred(owner, newOwner);
        owner = newOwner;
    }
}

/* ========================= ReentrancyGuard ========================= */
abstract contract ReentrancyGuard {
    uint256 private constant _NOT_ENTERED = 1;
    uint256 private constant _ENTERED = 2;
    uint256 private _status;
    
    constructor() { _status = _NOT_ENTERED; }
    
    modifier nonReentrant() {
        require(_status != _ENTERED, "ReentrancyGuard: reentrant");
        _status = _ENTERED;
        _;
        _status = _NOT_ENTERED;
    }
}

/* ========================= ERC20 Interface ========================= */
interface IERC20 {
    function balanceOf(address account) external view returns (uint256);
    function transfer(address to, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
}

/* ========================= SparkKnowledgeNFT ========================= */
contract SparkKnowledgeNFT is Ownable, ReentrancyGuard {
    
    // ============== 稀有度等级 ==============
    enum Rarity { Common, Rare, Epic, Legendary }
    
    // ============== 铸造参数结构（解决 Stack too deep）==============
    struct MintParams {
        string conversationId;
        string ragId;
        string ipfsCID;
        uint256 sparkValue;
        uint256 baseScore;
        uint256 citationScore;
        uint256 activationScore;
        uint256 behaviorScore;
        uint256 price;
    }
    
    // ============== NFT 结构 ==============
    struct SparkNFT {
        string  conversationId;
        string  ragId;
        string  ipfsCID;
        uint256 sparkValue;
        uint256 scores;         // 打包的分数 (base|citation|activation|behavior)
        Rarity  rarity;
        address creator;
        uint64  createdAt;
        bool    isActive;
        uint256 price;
        uint256 totalSales;
        uint256 totalRevenue;
    }
    
    // 质押信息
    struct StakeInfo {
        uint256 amount;
        uint256 stakedAt;
        uint256 lockPeriod;
        uint256 rewardRate;
    }
    
    // ============== 状态变量 ==============
    string public name = "Spark Knowledge NFT";
    string public symbol = "SPARK";
    uint256 public nextTokenId;
    
    mapping(uint256 => address) private _ownerOf;
    mapping(address => uint256) private _balanceOf;
    mapping(uint256 => address) private _tokenApprovals;
    mapping(address => mapping(address => bool)) private _operatorApprovals;
    
    mapping(uint256 => SparkNFT) public sparkNFTs;
    mapping(string => uint256) public conversationToToken;
    mapping(string => bool) public usedConversations;
    mapping(address => mapping(uint256 => bool)) public accessRights;
    mapping(uint256 => StakeInfo) public stakes;
    
    uint256 public totalStaked;
    
    IERC20 public utilityToken;
    address public platformAddress;
    address public daoAddress;
    address public trustedSigner;
    
    uint16 public platformFeeBps = 2000;
    uint16 public daoFeeBps = 500;
    uint256 public minSparkForMint = 70;
    uint32 public chainId;
    address public bridge;
    
    // ============== 事件 ==============
    event Transfer(address indexed from, address indexed to, uint256 indexed tokenId);
    event Approval(address indexed owner, address indexed spender, uint256 indexed tokenId);
    event ApprovalForAll(address indexed owner, address indexed operator, bool approved);
    event SparkNFTMinted(uint256 indexed tokenId, address indexed creator, string conversationId, uint256 sparkValue, Rarity rarity);
    event AccessPurchased(uint256 indexed tokenId, address indexed buyer, uint256 price);
    event NFTStaked(uint256 indexed tokenId, address indexed staker, uint256 amount);
    event NFTUnstaked(uint256 indexed tokenId, address indexed staker, uint256 amount);
    
    // ============== 构造函数 ==============
    constructor(
        address _utilityToken,
        address _platform,
        address _dao,
        address _trustedSigner,
        uint32 _chainId
    ) {
        require(_utilityToken != address(0), "NFT: zero token");
        require(_platform != address(0), "NFT: zero platform");
        require(_trustedSigner != address(0), "NFT: zero signer");
        
        utilityToken = IERC20(_utilityToken);
        platformAddress = _platform;
        daoAddress = _dao;
        trustedSigner = _trustedSigner;
        chainId = _chainId;
    }
    
    // ============== ERC721 基础函数 ==============
    function ownerOf(uint256 tokenId) public view returns (address) {
        address o = _ownerOf[tokenId];
        require(o != address(0), "ERC721: nonexistent");
        return o;
    }
    
    function balanceOf(address owner_) external view returns (uint256) {
        require(owner_ != address(0), "ERC721: zero addr");
        return _balanceOf[owner_];
    }
    
    function approve(address to, uint256 tokenId) external {
        address o = ownerOf(tokenId);
        require(msg.sender == o || _operatorApprovals[o][msg.sender], "ERC721: not approved");
        _tokenApprovals[tokenId] = to;
        emit Approval(o, to, tokenId);
    }
    
    function setApprovalForAll(address operator, bool approved) external {
        _operatorApprovals[msg.sender][operator] = approved;
        emit ApprovalForAll(msg.sender, operator, approved);
    }
    
    function transferFrom(address from, address to, uint256 tokenId) public {
        require(to != address(0), "ERC721: zero addr");
        address o = ownerOf(tokenId);
        require(o == from, "ERC721: from != owner");
        require(msg.sender == o || _tokenApprovals[tokenId] == msg.sender || _operatorApprovals[o][msg.sender], "ERC721: not approved");
        require(stakes[tokenId].amount == 0, "NFT: staked");
        
        _tokenApprovals[tokenId] = address(0);
        unchecked { _balanceOf[from] -= 1; _balanceOf[to] += 1; }
        _ownerOf[tokenId] = to;
        emit Transfer(from, to, tokenId);
    }
    
    // ============== 铸造函数（使用结构体参数）==============
    
    /**
     * @dev 铸造光源 NFT
     * @param params 铸造参数结构体
     * @param signature 后端签名
     */
    function mintSparkNFT(
        MintParams calldata params,
        bytes calldata signature
    ) external returns (uint256 tokenId) {
        // 验证
        require(bytes(params.conversationId).length > 0, "NFT: empty id");
        require(!usedConversations[params.conversationId], "NFT: minted");
        require(params.sparkValue >= minSparkForMint && params.sparkValue <= 100, "NFT: invalid spark");
        
        // 验证签名
        bytes32 msgHash = keccak256(abi.encodePacked(
            msg.sender,
            params.conversationId,
            params.ragId,
            params.sparkValue,
            params.baseScore,
            params.citationScore,
            params.activationScore,
            params.behaviorScore
        ));
        require(_verify(msgHash, signature), "NFT: invalid sig");
        
        // 铸造
        tokenId = nextTokenId++;
        _ownerOf[tokenId] = msg.sender;
        _balanceOf[msg.sender] += 1;
        
        // 打包分数以节省存储
        uint256 packedScores = (params.baseScore << 192) | 
                               (params.citationScore << 128) | 
                               (params.activationScore << 64) | 
                               params.behaviorScore;
        
        sparkNFTs[tokenId] = SparkNFT({
            conversationId: params.conversationId,
            ragId: params.ragId,
            ipfsCID: params.ipfsCID,
            sparkValue: params.sparkValue,
            scores: packedScores,
            rarity: _getRarity(params.sparkValue),
            creator: msg.sender,
            createdAt: uint64(block.timestamp),
            isActive: true,
            price: params.price,
            totalSales: 0,
            totalRevenue: 0
        });
        
        conversationToToken[params.conversationId] = tokenId;
        usedConversations[params.conversationId] = true;
        
        emit Transfer(address(0), msg.sender, tokenId);
        emit SparkNFTMinted(tokenId, msg.sender, params.conversationId, params.sparkValue, sparkNFTs[tokenId].rarity);
    }
    
    /**
     * @dev 简化版铸造（无签名验证，仅测试用）
     */
    function mintSimple(
        string calldata conversationId,
        uint256 sparkValue,
        uint256 price
    ) external returns (uint256 tokenId) {
        require(bytes(conversationId).length > 0, "NFT: empty id");
        require(!usedConversations[conversationId], "NFT: minted");
        require(sparkValue >= minSparkForMint && sparkValue <= 100, "NFT: invalid spark");
        
        tokenId = nextTokenId++;
        _ownerOf[tokenId] = msg.sender;
        _balanceOf[msg.sender] += 1;
        
        sparkNFTs[tokenId] = SparkNFT({
            conversationId: conversationId,
            ragId: "",
            ipfsCID: "",
            sparkValue: sparkValue,
            scores: 0,
            rarity: _getRarity(sparkValue),
            creator: msg.sender,
            createdAt: uint64(block.timestamp),
            isActive: true,
            price: price,
            totalSales: 0,
            totalRevenue: 0
        });
        
        conversationToToken[conversationId] = tokenId;
        usedConversations[conversationId] = true;
        
        emit Transfer(address(0), msg.sender, tokenId);
        emit SparkNFTMinted(tokenId, msg.sender, conversationId, sparkValue, sparkNFTs[tokenId].rarity);
    }
    
    function _getRarity(uint256 sparkValue) internal pure returns (Rarity) {
        if (sparkValue >= 85) return Rarity.Legendary;
        if (sparkValue >= 70) return Rarity.Epic;
        if (sparkValue >= 50) return Rarity.Rare;
        return Rarity.Common;
    }
    
    function _verify(bytes32 hash, bytes memory sig) internal view returns (bool) {
        require(sig.length == 65, "Invalid sig len");
        bytes32 ethHash = keccak256(abi.encodePacked("\x19Ethereum Signed Message:\n32", hash));
        bytes32 r; bytes32 s; uint8 v;
        assembly {
            r := mload(add(sig, 32))
            s := mload(add(sig, 64))
            v := byte(0, mload(add(sig, 96)))
        }
        if (v < 27) v += 27;
        return ecrecover(ethHash, v, r, s) == trustedSigner;
    }
    
    // ============== 访问权购买 ==============
    function purchaseAccess(uint256 tokenId) external nonReentrant {
        SparkNFT storage nft = sparkNFTs[tokenId];
        require(nft.isActive && nft.price > 0, "NFT: unavailable");
        require(!accessRights[msg.sender][tokenId], "NFT: owned");
        
        require(utilityToken.transferFrom(msg.sender, address(this), nft.price), "NFT: transfer failed");
        
        uint256 pFee = (nft.price * platformFeeBps) / 10000;
        uint256 dFee = (nft.price * daoFeeBps) / 10000;
        uint256 cShare = nft.price - pFee - dFee;
        
        if (cShare > 0) utilityToken.transfer(nft.creator, cShare);
        if (pFee > 0) utilityToken.transfer(platformAddress, pFee);
        if (dFee > 0 && daoAddress != address(0)) utilityToken.transfer(daoAddress, dFee);
        
        accessRights[msg.sender][tokenId] = true;
        nft.totalSales += 1;
        nft.totalRevenue += nft.price;
        
        emit AccessPurchased(tokenId, msg.sender, nft.price);
    }
    
    function hasAccess(address user, uint256 tokenId) external view returns (bool) {
        return accessRights[user][tokenId] || _ownerOf[tokenId] == user;
    }
    
    // ============== 质押 ==============
    function stakeNFT(uint256 tokenId, uint256 amount, uint256 lockDays) external {
        require(ownerOf(tokenId) == msg.sender, "NFT: not owner");
        require(amount > 0 && stakes[tokenId].amount == 0, "NFT: invalid stake");
        require(lockDays >= 7, "NFT: min 7 days");
        
        require(utilityToken.transferFrom(msg.sender, address(this), amount), "NFT: stake failed");
        
        stakes[tokenId] = StakeInfo({
            amount: amount,
            stakedAt: block.timestamp,
            lockPeriod: lockDays * 1 days,
            rewardRate: 5 + (sparkNFTs[tokenId].sparkValue / 10)
        });
        totalStaked += amount;
        
        emit NFTStaked(tokenId, msg.sender, amount);
    }
    
    function unstakeNFT(uint256 tokenId) external nonReentrant {
        StakeInfo memory s = stakes[tokenId];
        require(s.amount > 0 && ownerOf(tokenId) == msg.sender, "NFT: invalid");
        require(block.timestamp >= s.stakedAt + s.lockPeriod, "NFT: locked");
        
        uint256 reward = (s.amount * s.rewardRate * (block.timestamp - s.stakedAt)) / (100 * 365 days);
        delete stakes[tokenId];
        totalStaked -= s.amount;
        
        utilityToken.transfer(msg.sender, s.amount + reward);
        emit NFTUnstaked(tokenId, msg.sender, s.amount);
    }
    
    // ============== 价格管理 ==============
    function setPrice(uint256 tokenId, uint256 newPrice) external {
        require(ownerOf(tokenId) == msg.sender, "NFT: not owner");
        sparkNFTs[tokenId].price = newPrice;
    }
    
    function toggleActive(uint256 tokenId) external {
        require(ownerOf(tokenId) == msg.sender, "NFT: not owner");
        sparkNFTs[tokenId].isActive = !sparkNFTs[tokenId].isActive;
    }
    
    // ============== 查询 ==============
    function getNFTInfo(uint256 tokenId) external view returns (
        address owner_,
        SparkNFT memory nft,
        StakeInfo memory stake
    ) {
        owner_ = ownerOf(tokenId);
        nft = sparkNFTs[tokenId];
        stake = stakes[tokenId];
    }
    
    function getScores(uint256 tokenId) external view returns (
        uint256 base, uint256 citation, uint256 activation, uint256 behavior
    ) {
        uint256 packed = sparkNFTs[tokenId].scores;
        base = (packed >> 192) & 0xFFFFFFFFFFFFFFFF;
        citation = (packed >> 128) & 0xFFFFFFFFFFFFFFFF;
        activation = (packed >> 64) & 0xFFFFFFFFFFFFFFFF;
        behavior = packed & 0xFFFFFFFFFFFFFFFF;
    }
    
    function getRarityName(Rarity r) external pure returns (string memory) {
        if (r == Rarity.Legendary) return "Legendary";
        if (r == Rarity.Epic) return "Epic";
        if (r == Rarity.Rare) return "Rare";
        return "Common";
    }
    
    // ============== 管理 ==============
    function setConfig(uint16 _pFee, uint16 _dFee, uint256 _minSpark) external onlyOwner {
        require(_pFee + _dFee <= 5000, "NFT: fee high");
        platformFeeBps = _pFee;
        daoFeeBps = _dFee;
        minSparkForMint = _minSpark;
    }
    
    function setTrustedSigner(address signer) external onlyOwner {
        require(signer != address(0), "NFT: zero");
        trustedSigner = signer;
    }
    
    function setPlatformAddress(address p) external onlyOwner {
        require(p != address(0), "NFT: zero");
        platformAddress = p;
    }
    
    function setDaoAddress(address d) external onlyOwner {
        daoAddress = d;
    }
    
    function setBridge(address b) external onlyOwner {
        bridge = b;
    }
}
