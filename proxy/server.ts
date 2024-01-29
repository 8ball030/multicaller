import {ComputeBudgetProgram} from "@solana/web3.js";

const fs = require('fs');
const express = require('express');
const bs58 = require('bs58');
const fetch = require('cross-fetch');
const { Wallet } = require('@project-serum/anchor');
const { Connection, Keypair, PublicKey, VersionedTransaction, TransactionMessage, AddressLookupTableAccount, TransactionInstruction } = require('@solana/web3.js');

import Squads from "@sqds/sdk";

const rpc = 'https://api.mainnet-beta.solana.com';
// @ts-ignore
const key = process.env.SOLANA_PRIVATE_KEY.trim()
const keypair = Keypair.fromSecretKey(bs58.decode(key));
const wallet = new Wallet(keypair);

const port = 3000;
const app = express();
app.use(express.json())


const VAULT = 1;
const multisigAddress = new PublicKey(process.env.MULTISIG_ADDRESS);
const squadVault = process.env.VAULT_ADDRESS;
app.post('/tx', async (req: any, res: any) => {
    try {
        let {inputMint, outputMint, amount, slippageBps, priorityFee, timeoutInMs} = req.body
        if (timeoutInMs == undefined) {
            timeoutInMs = 60_000
        }
        const config = {
            confirmTransactionInitialTimeout: timeoutInMs,
        };
        const connection = new Connection(rpc, config);
        const squads = Squads.mainnet(wallet, config as any);

        const txBuilder = await squads.getTransactionBuilder(multisigAddress, VAULT);

        const url = `https://quote-api.jup.ag/v6/quote?inputMint=${inputMint}&outputMint=${outputMint}&amount=${amount}&slippageBps=${slippageBps}&onlyDirectRoutes=true&maxAccounts=30`;
        const quoteResponse = await (
            await fetch(url)
        ).json();
        const instructions = await (
            await fetch('https://quote-api.jup.ag/v6/swap-instructions', {
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
            })
        ).json();
        if (instructions.error) {
            throw new Error("Failed to get swap instructions: " + instructions.error);
        }

        if (priorityFee == undefined) {
            priorityFee = instructions.prioritizationFeeLamports
        }


        const {
            setupInstructions, // Setup missing ATA for the users.
            swapInstruction: swapInstructionPayload, // The actual swap instruction.
            cleanupInstruction, // Unwrap the SOL if `wrapAndUnwrapSol = true`.
            addressLookupTableAddresses, // The lookup table addresses that you can use if you are using versioned transaction.
        } = instructions;

        const deserializeInstruction = (instruction: any) => {
            return new TransactionInstruction({
                programId: new PublicKey(instruction.programId),
                keys: instruction.accounts.map((key: any) => ({
                    pubkey: new PublicKey(key.pubkey),
                    isSigner: key.isSigner,
                    isWritable: key.isWritable,
                })),
                data: Buffer.from(instruction.data, "base64"),
            });
        };

        const getAddressLookupTableAccounts = async (keys: any) => {
            const addressLookupTableAccountInfos =
                await connection.getMultipleAccountsInfo(
                    keys.map((key: any) => new PublicKey(key))
                );

            return addressLookupTableAccountInfos.reduce((acc: any, accountInfo: any, index: any) => {
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

        addressLookupTableAccounts.push(
            ...(await getAddressLookupTableAccounts(addressLookupTableAddresses))
        );

        const [instructions2, pda] = await txBuilder.withInstructions([
            ComputeBudgetProgram.setComputeUnitPrice({microLamports: priorityFee}),
            ...setupInstructions.map(deserializeInstruction),
        ]).getInstructions()
        const blockhash = (await connection.getLatestBlockhash()).blockhash;
        const messageV0 = new TransactionMessage({
            payerKey: wallet.payer.publicKey,
            recentBlockhash: blockhash,
            instructions: instructions2,
        }).compileToV0Message(addressLookupTableAccounts);
        let transaction = new VersionedTransaction(messageV0);
        transaction.sign([wallet.payer]);
        let rawTransaction = transaction.serialize();
        let txid = await connection.sendRawTransaction(rawTransaction, {
            maxRetries: 2,
        });
        await connection.confirmTransaction(txid);
        console.log("Confirmed transaction")
        await squads.addInstruction(pda, deserializeInstruction(swapInstructionPayload))
        console.log("Added swap instruction")
        await squads.addInstruction(pda, deserializeInstruction(cleanupInstruction))
        console.log("Added cleanup instruction")

        console.log(`https://solscan.io/tx/${txid}`);
        const activate = await squads.buildActivateTransaction(multisigAddress, pda)
        const approve = await squads.buildApproveTransaction(multisigAddress, pda)
        const execute = await squads.buildExecuteInstruction(multisigAddress, pda)

        const txMessage = new TransactionMessage({
            payerKey: wallet.payer.publicKey,
            recentBlockhash: blockhash,
            instructions: [
                ComputeBudgetProgram.setComputeUnitPrice({microLamports: priorityFee}),
                activate,
                approve,
                execute
            ],
        }).compileToV0Message(addressLookupTableAccounts);
        transaction = new VersionedTransaction(txMessage);
        transaction.sign([wallet.payer]);
        rawTransaction = transaction.serialize();
        txid = await connection.sendRawTransaction(rawTransaction, {
            maxRetries: 2,
        });
        await connection.confirmTransaction(txid);
        res.json({"status": "ok", "txId": pda, "url": `https://solscan.io/tx/${pda}`})
    } catch (e: any) {
        console.log(e)
        res.status(500).json({"status": "error", "message": e.message})
    }

});

app.use(express.json());
app.listen(port, () => {
    console.log(`Server is running on http://localhost:${port}`);
});