// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title UtilityToken
 * @dev 平台实用代币 - ERC20 标准实现
 * 
 * 用途：
 * - NFT 访问权购买
 * - 质押奖励
 * - 平台费用支付
 */

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

contract UtilityToken is Ownable {
    string public name = "Spark Utility Token";
    string public symbol = "SUTIL";
    uint8 public decimals = 18;

    uint256 public totalSupply;

    mapping(address => uint256) private _bal;
    mapping(address => mapping(address => uint256)) private _allow;

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);

    function balanceOf(address a) external view returns (uint256) { 
        return _bal[a]; 
    }
    
    function allowance(address o, address s) external view returns (uint256) { 
        return _allow[o][s]; 
    }

    function approve(address spender, uint256 value) external returns (bool) {
        _allow[msg.sender][spender] = value;
        emit Approval(msg.sender, spender, value);
        return true;
    }

    function transfer(address to, uint256 value) external returns (bool) {
        _transfer(msg.sender, to, value);
        return true;
    }

    function transferFrom(address from, address to, uint256 value) external returns (bool) {
        uint256 a = _allow[from][msg.sender];
        require(a >= value, "ERC20: allowance");
        unchecked { _allow[from][msg.sender] = a - value; }
        _transfer(from, to, value);
        return true;
    }

    /**
     * @dev 铸造代币（仅 owner）
     * @param to 接收地址
     * @param value 数量（包含 18 位小数）
     * 
     * 示例：铸造 1000 个代币
     * value = 1000 * 10^18 = 1000000000000000000000
     */
    function mint(address to, uint256 value) external onlyOwner {
        require(to != address(0), "ERC20: zero addr");
        totalSupply += value;
        _bal[to] += value;
        emit Transfer(address(0), to, value);
    }

    /**
     * @dev 销毁代币（仅 owner）
     */
    function burn(address from, uint256 value) external onlyOwner {
        require(_bal[from] >= value, "ERC20: balance");
        unchecked { _bal[from] -= value; }
        totalSupply -= value;
        emit Transfer(from, address(0), value);
    }

    function _transfer(address from, address to, uint256 value) internal {
        require(to != address(0), "ERC20: zero addr");
        require(_bal[from] >= value, "ERC20: balance");
        unchecked { _bal[from] -= value; _bal[to] += value; }
        emit Transfer(from, to, value);
    }
}

