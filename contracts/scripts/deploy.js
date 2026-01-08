const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  console.log("🚀 Starting RAG Knowledge NFT deployment...\n");
  
  // 获取部署账户
  const [deployer] = await hre.ethers.getSigners();
  console.log("📍 Deployer address:", deployer.address);
  
  // 获取余额
  const balance = await hre.ethers.provider.getBalance(deployer.address);
  console.log("💰 Deployer balance:", hre.ethers.formatEther(balance), "ETH\n");
  
  if (balance === 0n) {
    console.error("❌ Deployer has no balance! Please fund the account first.");
    console.log("\n🔗 Faucets:");
    console.log("   Sepolia: https://sepoliafaucet.com");
    console.log("   Polygon Amoy: https://faucet.polygon.technology");
    console.log("   Base Sepolia: https://www.coinbase.com/faucets/base-ethereum-sepolia-faucet");
    process.exit(1);
  }
  
  // 部署合约
  console.log("📝 Deploying RAGKnowledgeNFT contract...");
  
  const RAGKnowledgeNFT = await hre.ethers.getContractFactory("RAGKnowledgeNFT");
  const nft = await RAGKnowledgeNFT.deploy();
  
  await nft.waitForDeployment();
  
  const contractAddress = await nft.getAddress();
  console.log("✅ RAGKnowledgeNFT deployed to:", contractAddress);
  
  // 获取网络信息
  const network = await hre.ethers.provider.getNetwork();
  console.log("\n📊 Network:", network.name);
  console.log("🔗 Chain ID:", network.chainId.toString());
  
  // 生成部署信息文件
  const deploymentInfo = {
    network: network.name,
    chainId: network.chainId.toString(),
    contractAddress: contractAddress,
    deployer: deployer.address,
    deployedAt: new Date().toISOString(),
    blockNumber: await hre.ethers.provider.getBlockNumber(),
    transactionHash: nft.deploymentTransaction()?.hash
  };
  
  // 保存到文件
  const deploymentsDir = path.join(__dirname, "..", "deployments");
  if (!fs.existsSync(deploymentsDir)) {
    fs.mkdirSync(deploymentsDir, { recursive: true });
  }
  
  const deploymentFile = path.join(deploymentsDir, `${network.name}.json`);
  fs.writeFileSync(deploymentFile, JSON.stringify(deploymentInfo, null, 2));
  console.log("\n📁 Deployment info saved to:", deploymentFile);
  
  // 生成后端配置
  const backendEnvUpdate = `
# Web3 Configuration (add to .env)
WEB3_ENABLED=true
WEB3_NETWORK=${network.name}
WEB3_CHAIN_ID=${network.chainId}
RAG_NFT_CONTRACT=${contractAddress}
`;
  
  console.log("\n📋 Add to your backend .env file:");
  console.log(backendEnvUpdate);
  
  // 验证合约（如果不是本地网络）
  if (network.chainId !== 31337n) {
    console.log("\n⏳ Waiting for block confirmations...");
    await new Promise(resolve => setTimeout(resolve, 30000)); // 等待 30 秒
    
    console.log("🔍 Verifying contract on Etherscan...");
    try {
      await hre.run("verify:verify", {
        address: contractAddress,
        constructorArguments: []
      });
      console.log("✅ Contract verified!");
    } catch (error) {
      console.log("⚠️ Verification failed:", error.message);
      console.log("   You can verify manually later with:");
      console.log(`   npx hardhat verify --network ${network.name} ${contractAddress}`);
    }
  }
  
  // 生成前端配置
  const frontendConfig = {
    contractAddress: contractAddress,
    chainId: Number(network.chainId),
    networkName: network.name,
    abi: JSON.parse(
      fs.readFileSync(
        path.join(__dirname, "..", "artifacts", "src", "RAGKnowledgeNFT.sol", "RAGKnowledgeNFT.json")
      )
    ).abi
  };
  
  const frontendConfigFile = path.join(deploymentsDir, "frontend-config.json");
  fs.writeFileSync(frontendConfigFile, JSON.stringify(frontendConfig, null, 2));
  console.log("\n📁 Frontend config saved to:", frontendConfigFile);
  
  console.log("\n🎉 Deployment complete!");
  console.log("\n📚 Next steps:");
  console.log("   1. Copy the contract address to your .env file");
  console.log("   2. Copy frontend-config.json to your frontend project");
  console.log("   3. Fund the contract if needed for operations");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("❌ Deployment failed:", error);
    process.exit(1);
  });

