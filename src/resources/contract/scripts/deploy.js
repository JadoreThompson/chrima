const hre = require("hardhat");

async function main() {
  const contractName = process.env.CONTRACT_NAME || "ChrimaPayment";
  const constructorArgs = process.env.CONSTRUCTOR_ARGS
    ? JSON.parse(process.env.CONSTRUCTOR_ARGS)
    : [];

  const factory = await hre.ethers.getContractFactory(contractName);
  console.log(`Deploying ${contractName} ...`);
  const contract = await factory.deploy(...constructorArgs);
  console.log("Transaction submitted, waiting for confirmation ...");

  await contract.waitForDeployment();

  const address = await contract.getAddress();
  console.log(`${contractName} deployed to:`, address);
  if (constructorArgs.length > 0) {
    console.log(`Constructor args:`, constructorArgs);
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
