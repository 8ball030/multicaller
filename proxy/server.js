"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
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
const squads = sdk_1.default.mainnet(wallet);
const port = 3000;
const app = express();
app.use(express.json());
const multisigAddress = new PublicKey('9UNKk1HWAQEh8XNxSf3qWiptmMmDiYxf4i7NPDbj4YBU');
const VAULT = 1;
const squadVault = "39Zh4C687EXLY7CT8gjCxe2hUc3krESjUsqs7A1CKD5E";
app.post('/tx', async (req, res) => {
    try {
        const txBuilder = await squads.getTransactionBuilder(multisigAddress, VAULT);
        console.log(req.body);
        const { inputMint, outputMint, amount, slippageBps } = req.body;
        const connection = new Connection(rpc);
        const url = `https://quote-api.jup.ag/v6/quote?inputMint=${inputMint}&outputMint=${outputMint}&amount=${amount}&slippageBps=${slippageBps}&onlyDirectRoutes=true&maxAccounts=30`;
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
        const [instructions2, pda] = await txBuilder.withInstructions([
            ...setupInstructions.map(deserializeInstruction),
        ]).getInstructions();
        console.log(pda);
        const blockhash = (await connection.getLatestBlockhash()).blockhash;
        console.log(wallet.payer.publicKey);
        const messageV0 = new TransactionMessage({
            payerKey: wallet.payer.publicKey,
            recentBlockhash: blockhash,
            instructions: instructions2,
        }).compileToV0Message(addressLookupTableAccounts);
        const transaction = new VersionedTransaction(messageV0);
        transaction.sign([wallet.payer]);
        const rawTransaction = transaction.serialize();
        const txid = await connection.sendRawTransaction(rawTransaction, {
            maxRetries: 2,
        });
        await connection.confirmTransaction(txid);
        await squads.addInstruction(pda, deserializeInstruction(swapInstructionPayload));
        console.log("Added swap instruction");
        await squads.addInstruction(pda, deserializeInstruction(cleanupInstruction));
        console.log("Added cleanup instruction");
        console.log(`https://solscan.io/tx/${txid}`);
        await squads.activateTransaction(pda);
        await squads.approveTransaction(pda);
        await squads.executeTransaction(pda);
        res.json({ "status": "ok", "txId": pda, "url": `https://solscan.io/tx/${pda}` });
    }
    catch (e) {
        console.log(e);
        res.json({ "status": "error", "message": e.message });
    }
});
app.use(express.json());
app.listen(port, () => {
    console.log(`Server is running on http://localhost:${port}`);
});
