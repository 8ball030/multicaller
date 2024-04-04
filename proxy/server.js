"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = __importDefault(require("express"));
const web3_js_1 = require("@solana/web3.js");
const bs58_1 = __importDefault(require("bs58"));
const cross_fetch_1 = __importDefault(require("cross-fetch"));
const anchor_1 = require("@project-serum/anchor");
const multisig = __importStar(require("@sqds/multisig"));
const rpc = 'https://api.mainnet-beta.solana.com';
const pkeyEnv = process.env.SOLANA_PRIVATE_KEY;
if (pkeyEnv === undefined) {
    throw new Error("Environment variable `SOLANA_PRIVATE_KEY` not set.");
}
const pkey = pkeyEnv.trim();
const keypair = web3_js_1.Keypair.fromSecretKey(bs58_1.default.decode(pkey));
const feePayer = new anchor_1.Wallet(keypair).payer;
const port = 3000;
const app = (0, express_1.default)();
app.use(express_1.default.json());
// number of ephemeral signing PDAs required by the transaction
const base64 = "base64";
const ephemeralSigners = 0;
const vaultIndex = 0;
const internalServerErrorCode = 500;
const multisigAddressEnv = process.env.MULTISIG_ADDRESS;
if (multisigAddressEnv === undefined) {
    throw new Error("Environment variable `MULTISIG_ADDRESS` not set.");
}
const multisigAddress = new web3_js_1.PublicKey(multisigAddressEnv);
const vaultEnv = process.env.VAULT_ADDRESS;
if (vaultEnv === undefined) {
    throw new Error("Environment variable `VAULT_ADDRESS` not set.");
}
const squadVault = new web3_js_1.PublicKey(vaultEnv);
/**
 * Get the multisig's index for the next transaction.
 */
const getTransactionIndex = async (connection) => {
    const multisigAccount = await multisig.accounts.Multisig.fromAccountAddress(connection, multisigAddress);
    return multisig.utils.toBigInt(multisigAccount.transactionIndex) + 1n;
};
app.post('/tx', async (req, res) => {
    try {
        let { inputMint, outputMint, amount, slippageBps, priorityFee, timeoutInMs, maxRetries } = req.body;
        if (timeoutInMs === undefined) {
            timeoutInMs = 60000;
        }
        if (maxRetries === undefined) {
            maxRetries = 5;
        }
        const config = {
            confirmTransactionInitialTimeout: timeoutInMs,
        };
        const connection = new web3_js_1.Connection(rpc, config);
        // get a quote from the Jupiter API, required to construct the instructions for the swap
        const url = `https://quote-api.jup.ag/v6/quote?inputMint=${inputMint}&outputMint=${outputMint}&amount=${amount}&slippageBps=${slippageBps}&onlyDirectRoutes=true&maxAccounts=10`;
        const quoteResponse = await (await (0, cross_fetch_1.default)(url)).json();
        // get the instructions for the swap from the Jupiter API, using the retrieved quote
        const instructions = await (await (0, cross_fetch_1.default)('https://quote-api.jup.ag/v6/swap-instructions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                // quoteResponse from /quote api
                quoteResponse,
                userPublicKey: squadVault.toString(),
                prioritizationFeeLamports: 'auto' // or custom lamports: 1000
            })
        })).json();
        if (instructions.error) {
            throw new Error("Failed to get swap instructions: " + instructions.error);
        }
        if (priorityFee == undefined) {
            priorityFee = instructions.prioritizationFeeLamports;
        }
        const { setupInstructions, // Setup missing ATA for the users.
        swapInstruction: swapInstructionPayload, // The actual swap instruction.
        cleanupInstruction, // Unwrap the SOL if `wrapAndUnwrapSol = true`.
        addressLookupTableAddresses, // The lookup table addresses to be used for versioned transactions.
         } = instructions;
        /**
         Deserialize the instructions returned from the Jupiter API into the format expected by the squads SDK
         */
        const deserializeInstruction = (instruction) => {
            return new web3_js_1.TransactionInstruction({
                programId: new web3_js_1.PublicKey(instruction.programId),
                keys: instruction.accounts.map((key) => ({
                    pubkey: new web3_js_1.PublicKey(key.pubkey),
                    isSigner: key.isSigner,
                    isWritable: key.isWritable,
                })),
                data: Buffer.from(instruction.data, base64),
            });
        };
        /**
         * Get address lookup table accounts using the addresses returned by the Jupiter API
         * @param keys the addresses returned by the Jupiter API
         */
        const getAddressLookupTableAccounts = async (keys) => {
            const addressLookupTableAccountInfos = await connection.getMultipleAccountsInfo(keys.map((key) => new web3_js_1.PublicKey(key)));
            return addressLookupTableAccountInfos.reduce((acc, accountInfo, index) => {
                const addressLookupTableAddress = keys[index];
                if (accountInfo) {
                    const addressLookupTableAccount = new web3_js_1.AddressLookupTableAccount({
                        key: new web3_js_1.PublicKey(addressLookupTableAddress),
                        state: web3_js_1.AddressLookupTableAccount.deserialize(accountInfo.data),
                    });
                    acc.push(addressLookupTableAccount);
                }
                return acc;
            }, []);
        };
        // get the address lookup table accounts
        const addressLookupTableAccounts = [];
        addressLookupTableAccounts.push(...(await getAddressLookupTableAccounts(addressLookupTableAddresses)));
        // create an instruction to set the priority fee
        const priorityFeeInstruction = web3_js_1.ComputeBudgetProgram.setComputeUnitPrice({ microLamports: priorityFee });
        // create the swap instructions for a squads transaction, using the instructions returned by the Jupiter API
        const swapInstructions = [
            ...setupInstructions.map(deserializeInstruction),
            deserializeInstruction(swapInstructionPayload),
            deserializeInstruction(cleanupInstruction)
        ];
        // get the latest block's hash
        const blockhash = await connection.getLatestBlockhash();
        // create a swap tx message - no need to compile it to v0, this is done by `vaultTransactionCreate` below
        const swapMessage = new web3_js_1.TransactionMessage({
            payerKey: squadVault,
            recentBlockhash: blockhash.blockhash,
            instructions: swapInstructions,
        });
        // get the multisig's PDA
        const multisigPda = multisigAddress;
        // get the transaction's index
        let transactionIndex = await getTransactionIndex(connection);
        // create a vault transaction for the swap
        const createInstructions = multisig.instructions.vaultTransactionCreate({
            multisigPda,
            transactionIndex,
            creator: feePayer.publicKey,
            vaultIndex,
            ephemeralSigners,
            transactionMessage: swapMessage,
            addressLookupTableAccounts,
        });
        const messageV0 = new web3_js_1.TransactionMessage({
            payerKey: feePayer.publicKey,
            recentBlockhash: blockhash.blockhash,
            instructions: [
                priorityFeeInstruction,
                createInstructions,
            ],
        }).compileToV0Message();
        const tx = new web3_js_1.VersionedTransaction(messageV0);
        tx.sign([feePayer, ...[]]);
        let txSignature;
        try {
            txSignature = await connection.sendTransaction(tx);
            await connection.confirmTransaction(txSignature);
            console.log("Created squad transaction.");
        }
        catch (err) {
            console.log(err);
        }
        // propose the transaction for approval/rejection
        await multisig.rpc.proposalCreate({
            connection,
            feePayer,
            creator: feePayer,
            multisigPda,
            transactionIndex,
            sendOptions: { maxRetries: maxRetries },
        });
        await connection.confirmTransaction(txSignature);
        console.log("Created proposal for the transaction.");
        // approve the proposal
        await multisig.rpc.proposalApprove({
            connection,
            feePayer,
            member: feePayer,
            multisigPda,
            transactionIndex,
            sendOptions: { maxRetries: maxRetries },
        });
        await connection.confirmTransaction(txSignature);
        console.log("Approved proposal.");
        // execute the transaction
        await multisig.rpc.vaultTransactionExecute({
            connection,
            feePayer,
            member: feePayer.publicKey,
            multisigPda,
            transactionIndex,
            sendOptions: { maxRetries: maxRetries },
        });
        await connection.confirmTransaction(txSignature);
        console.log("Transaction executed.");
        res.json({ "status": "ok", "txId": txSignature, "url": `https://solscan.io/tx/${txSignature}` });
    }
    catch (e) {
        console.log(e);
        res.status(internalServerErrorCode).json({ "status": "error", "message": e.message });
    }
});
app.use(express_1.default.json());
app.listen(port, () => {
    console.log(`Server is running on http://localhost:${port}`);
});
