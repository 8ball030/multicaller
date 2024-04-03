"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const web3_js_1 = require("@solana/web3.js");
const fs = require('fs');
const express = require('express');
const bs58 = require('bs58');
const fetch = require('cross-fetch');
const { Wallet } = require('@project-serum/anchor');
const { Connection, Keypair, PublicKey, VersionedTransaction, TransactionMessage, AddressLookupTableAccount, TransactionInstruction } = require('@solana/web3.js');
const sdk_1 = __importDefault(require("@sqds/sdk"));
const rpc = 'https://api.mainnet-beta.solana.com';
// @ts-ignore
const key = process.env.SOLANA_PRIVATE_KEY.trim();
const keypair = Keypair.fromSecretKey(bs58.decode(key));
const wallet = new Wallet(keypair);
const port = 3000;
const app = express();
app.use(express.json());
const VAULT = 1;
const multisigAddress = new PublicKey(process.env.MULTISIG_ADDRESS);
const squadVault = process.env.VAULT_ADDRESS;
const sendTX = async (connection, instructions, addressLookupTableAccounts) => {
    let blockhash = (await connection.getLatestBlockhash()).blockhash;
    const messageV0 = new TransactionMessage({
        payerKey: wallet.payer.publicKey,
        recentBlockhash: blockhash,
        instructions: instructions,
    }).compileToV0Message(addressLookupTableAccounts);
    let transaction = new VersionedTransaction(messageV0);
    transaction.sign([wallet.payer]);
    let rawTransaction = transaction.serialize();
    let txid = await connection.sendRawTransaction(rawTransaction, {
        maxRetries: 2,
    });
    await connection.confirmTransaction(txid);
    console.log(`Confirmed ${txid}. https://solscan.io/tx/${txid}`);
};
const sendTXWithRetry = async (connection, instructions, addressLookupTableAccounts, maxRetries = 5) => {
    try {
        await sendTX(connection, instructions, addressLookupTableAccounts);
    }
    catch (e) {
        console.log(e);
        if (maxRetries > 0) {
            // Wait for 3 seconds
            const three_seconds = 3000;
            await new Promise(resolve => setTimeout(resolve, three_seconds));
            await sendTXWithRetry(connection, instructions, addressLookupTableAccounts, maxRetries - 1);
        }
        else {
            throw e;
        }
    }
};
app.post('/tx', async (req, res) => {
    try {
        let { inputMint, outputMint, amount, slippageBps, priorityFee, timeoutInMs, maxRetries } = req.body;
        if (timeoutInMs == undefined) {
            timeoutInMs = 60000;
        }
        if (maxRetries == undefined) {
            maxRetries = 5;
        }
        const config = {
            confirmTransactionInitialTimeout: timeoutInMs,
        };
        const connection = new Connection(rpc, config);
        const squads = sdk_1.default.mainnet(wallet, config);
        const txBuilder = await squads.getTransactionBuilder(multisigAddress, VAULT);
        const url = `https://quote-api.jup.ag/v6/quote?inputMint=${inputMint}&outputMint=${outputMint}&amount=${amount}&slippageBps=${slippageBps}&onlyDirectRoutes=true&maxAccounts=10`;
        const quoteResponse = await (await fetch(url)).json();
        const instructions = await (await fetch('https://quote-api.jup.ag/v6/swap-instructions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                // quoteResponse from /quote api
                quoteResponse,
                userPublicKey: squadVault,
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
        addressLookupTableAddresses, // The lookup table addresses that you can use if you are using versioned transaction.
         } = instructions;
        const deserializeInstruction = (instruction) => {
            return new TransactionInstruction({
                programId: new PublicKey(instruction.programId),
                keys: instruction.accounts.map((key) => ({
                    pubkey: new PublicKey(key.pubkey),
                    isSigner: key.isSigner,
                    isWritable: key.isWritable,
                })),
                data: Buffer.from(instruction.data, "base64"),
            });
        };
        const getAddressLookupTableAccounts = async (keys) => {
            const addressLookupTableAccountInfos = await connection.getMultipleAccountsInfo(keys.map((key) => new PublicKey(key)));
            return addressLookupTableAccountInfos.reduce((acc, accountInfo, index) => {
                const addressLookupTableAddress = keys[index];
                if (accountInfo) {
                    const addressLookupTableAccount = new AddressLookupTableAccount({
                        key: new PublicKey(addressLookupTableAddress),
                        state: AddressLookupTableAccount.deserialize(accountInfo.data),
                    });
                    acc.push(addressLookupTableAccount);
                }
                return acc;
            }, []);
        };
        const addressLookupTableAccounts = [];
        addressLookupTableAccounts.push(...(await getAddressLookupTableAccounts(addressLookupTableAddresses)));
        const priorityFeeInstruction = web3_js_1.ComputeBudgetProgram.setComputeUnitPrice({ microLamports: priorityFee });
        const [instructions2, pda] = await txBuilder.withInstructions([
            ...setupInstructions.map(deserializeInstruction),
        ]).getInstructions();
        await sendTXWithRetry(connection, [priorityFeeInstruction, ...instructions2], addressLookupTableAccounts, maxRetries);
        console.log("Created squad transaction");
        const transaction = await squads.getTransaction(pda);
        const addInstruction = await squads.buildAddInstruction(multisigAddress, pda, deserializeInstruction(swapInstructionPayload), transaction.instructionIndex + 1);
        await sendTXWithRetry(connection, [
            priorityFeeInstruction,
            addInstruction,
        ], addressLookupTableAccounts, maxRetries);
        console.log("Added swap instruction");
        const activate = await squads.buildActivateTransaction(multisigAddress, pda);
        const approve = await squads.buildApproveTransaction(multisigAddress, pda);
        const execute = await squads.buildExecuteInstruction(multisigAddress, pda);
        await sendTXWithRetry(connection, [
            priorityFeeInstruction,
            deserializeInstruction(cleanupInstruction),
            activate,
            approve,
            execute,
        ], addressLookupTableAccounts, maxRetries);
        console.log("Done");
        res.json({ "status": "ok", "txId": pda, "url": `https://solscan.io/tx/${pda}` });
    }
    catch (e) {
        console.log(e);
        res.status(500).json({ "status": "error", "message": e.message });
    }
});
app.use(express.json());
app.listen(port, () => {
    console.log(`Server is running on http://localhost:${port}`);
});
