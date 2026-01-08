const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("RAGKnowledgeNFT", function () {
  let nft;
  let owner;
  let user1;
  let user2;
  
  const MINT_FEE = ethers.parseEther("0.001");
  
  beforeEach(async function () {
    [owner, user1, user2] = await ethers.getSigners();
    
    const RAGKnowledgeNFT = await ethers.getContractFactory("RAGKnowledgeNFT");
    nft = await RAGKnowledgeNFT.deploy();
    await nft.waitForDeployment();
  });
  
  describe("Deployment", function () {
    it("Should set the right name and symbol", async function () {
      expect(await nft.name()).to.equal("RAG Knowledge NFT");
      expect(await nft.symbol()).to.equal("RAGNFT");
    });
    
    it("Should set the right owner", async function () {
      expect(await nft.owner()).to.equal(owner.address);
    });
    
    it("Should set the correct mint fee", async function () {
      expect(await nft.mintFee()).to.equal(MINT_FEE);
    });
  });
  
  describe("Minting", function () {
    const question = "What is the meaning of life?";
    const answer = "42";
    const answerHash = ethers.keccak256(ethers.toUtf8Bytes(answer));
    const ipfsCID = "QmTest123456789";
    
    it("Should mint a new NFT", async function () {
      await nft.connect(user1).mintKnowledgeNFT(
        question,
        answerHash,
        ipfsCID,
        { value: MINT_FEE }
      );
      
      expect(await nft.totalSupply()).to.equal(1);
      expect(await nft.ownerOf(1)).to.equal(user1.address);
    });
    
    it("Should store content correctly", async function () {
      await nft.connect(user1).mintKnowledgeNFT(
        question,
        answerHash,
        ipfsCID,
        { value: MINT_FEE }
      );
      
      const content = await nft.getContentDetails(1);
      expect(content.question).to.equal(question);
      expect(content.answerHash).to.equal(answerHash);
      expect(content.ipfsCID).to.equal(ipfsCID);
      expect(content.creator).to.equal(user1.address);
    });
    
    it("Should fail without sufficient fee", async function () {
      await expect(
        nft.connect(user1).mintKnowledgeNFT(
          question,
          answerHash,
          ipfsCID,
          { value: ethers.parseEther("0.0001") }
        )
      ).to.be.revertedWith("Insufficient mint fee");
    });
    
    it("Should prevent duplicate content", async function () {
      await nft.connect(user1).mintKnowledgeNFT(
        question,
        answerHash,
        ipfsCID,
        { value: MINT_FEE }
      );
      
      await expect(
        nft.connect(user2).mintKnowledgeNFT(
          "Different question",
          answerHash, // Same hash
          "QmDifferent",
          { value: MINT_FEE }
        )
      ).to.be.revertedWith("Content already minted");
    });
    
    it("Should refund excess payment", async function () {
      const excessPayment = ethers.parseEther("0.01");
      const balanceBefore = await ethers.provider.getBalance(user1.address);
      
      const tx = await nft.connect(user1).mintKnowledgeNFT(
        question,
        answerHash,
        ipfsCID,
        { value: excessPayment }
      );
      
      const receipt = await tx.wait();
      const gasUsed = receipt.gasUsed * receipt.gasPrice;
      
      const balanceAfter = await ethers.provider.getBalance(user1.address);
      const expectedBalance = balanceBefore - MINT_FEE - gasUsed;
      
      expect(balanceAfter).to.be.closeTo(expectedBalance, ethers.parseEther("0.0001"));
    });
    
    it("Should emit KnowledgeNFTMinted event", async function () {
      await expect(
        nft.connect(user1).mintKnowledgeNFT(
          question,
          answerHash,
          ipfsCID,
          { value: MINT_FEE }
        )
      ).to.emit(nft, "KnowledgeNFTMinted")
        .withArgs(1, user1.address, question, answerHash, ipfsCID);
    });
  });
  
  describe("Verification", function () {
    const question = "Test question";
    const answer = "Test answer";
    const answerHash = ethers.keccak256(ethers.toUtf8Bytes(answer));
    const ipfsCID = "QmTestCID";
    
    beforeEach(async function () {
      await nft.connect(user1).mintKnowledgeNFT(
        question,
        answerHash,
        ipfsCID,
        { value: MINT_FEE }
      );
    });
    
    it("Should verify correct content", async function () {
      const isValid = await nft.verifyContent(1, answer);
      expect(isValid).to.be.true;
    });
    
    it("Should reject incorrect content", async function () {
      const isValid = await nft.verifyContent(1, "Wrong answer");
      expect(isValid).to.be.false;
    });
    
    it("Should allow marking as verified", async function () {
      await nft.connect(user1).markVerified(1);
      
      const content = await nft.getContentDetails(1);
      expect(content.verified).to.be.true;
    });
  });
  
  describe("Token URI", function () {
    it("Should return correct IPFS URI", async function () {
      const ipfsCID = "QmTestCID123";
      const answerHash = ethers.keccak256(ethers.toUtf8Bytes("test"));
      
      await nft.connect(user1).mintKnowledgeNFT(
        "Question",
        answerHash,
        ipfsCID,
        { value: MINT_FEE }
      );
      
      expect(await nft.tokenURI(1)).to.equal(`ipfs://${ipfsCID}`);
    });
  });
  
  describe("User Tokens", function () {
    it("Should track user tokens", async function () {
      const answerHash1 = ethers.keccak256(ethers.toUtf8Bytes("answer1"));
      const answerHash2 = ethers.keccak256(ethers.toUtf8Bytes("answer2"));
      
      await nft.connect(user1).mintKnowledgeNFT(
        "Q1", answerHash1, "CID1", { value: MINT_FEE }
      );
      await nft.connect(user1).mintKnowledgeNFT(
        "Q2", answerHash2, "CID2", { value: MINT_FEE }
      );
      
      const tokens = await nft.getUserTokens(user1.address);
      expect(tokens.length).to.equal(2);
      expect(tokens[0]).to.equal(1);
      expect(tokens[1]).to.equal(2);
    });
  });
  
  describe("Admin Functions", function () {
    it("Should allow owner to update mint fee", async function () {
      const newFee = ethers.parseEther("0.002");
      await nft.setMintFee(newFee);
      expect(await nft.mintFee()).to.equal(newFee);
    });
    
    it("Should allow owner to withdraw", async function () {
      // Mint to add funds
      const answerHash = ethers.keccak256(ethers.toUtf8Bytes("test"));
      await nft.connect(user1).mintKnowledgeNFT(
        "Q", answerHash, "CID", { value: MINT_FEE }
      );
      
      const balanceBefore = await ethers.provider.getBalance(owner.address);
      await nft.withdraw();
      const balanceAfter = await ethers.provider.getBalance(owner.address);
      
      expect(balanceAfter).to.be.gt(balanceBefore);
    });
    
    it("Should prevent non-owner from admin functions", async function () {
      await expect(
        nft.connect(user1).setMintFee(ethers.parseEther("0.1"))
      ).to.be.revertedWith("Ownable: caller is not the owner");
    });
  });
});

