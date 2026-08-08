const hre = require("hardhat");

async function main() {
  const contractName = process.env.CONTRACT_NAME || "ChrimaPayment";

  const factory = await hre.ethers.getContractFactory(contractName);
  console.log(`Deploying ${contractName} ...`);

  const contract = await factory.deploy();
  console.log("Transaction submitted, waiting for confirmation ...");

  await contract.waitForDeployment();

  const address = await contract.getAddress();
  console.log(`${contractName} deployed to:`, address);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
