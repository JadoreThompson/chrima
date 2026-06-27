const hre = require("hardhat");

async function main() {
  const ChrimaPayment = await hre.ethers.getContractFactory("ChrimaPayment");
  const contract = await ChrimaPayment.deploy();

  await contract.waitForDeployment();

  const address = await contract.getAddress();
  console.log("ChrimaPayment deployed to:", address);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
