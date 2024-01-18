import fs from 'fs'
import bs58 from 'bs58'
import fetch from 'cross-fetch'
import { Wallet } from '@project-serum/anchor'
import { Connection, Keypair, PublicKey, VersionedTransaction, TransactionMessage, AddressLookupTableAccount, TransactionInstruction, clusterApiUrl, MessageAddressTableLookup } from '@solana/web3.js'

import { rpc } from "@sqds/multisig"
const express = require('express')

const VAULT = 1;

const key = fs.readFileSync('./solana_private_key.txt', 'utf-8').trim()
const keypair = Keypair.fromSecretKey(bs58.decode(key));
const wallet = new Wallet(keypair);
const multisigAddressStr = fs.readFileSync('./multisig_address', 'utf-8').trim();
const squadVault = fs.readFileSync('./multisig_vault', 'utf-8').trim();
const multisigAddress = new PublicKey(multisigAddressStr)

const port = 3000;
const app = express();
app.use(express.json())

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

async function getSwap({ inputMint, outputMint, amount, slippageBps }: {
    inputMint: string,
    outputMint: string,
    amount: number,
    slippageBps: number,
}) {
    const url = `https://quote-api.jup.ag/v6/quote?inputMint=${inputMint}&outputMint=${outputMint}&amount=${amount}&slippageBps=${slippageBps}`;
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
                quoteResponse,
                userPublicKey: squadVault,
                prioritizationFeeLamports: 'auto'
            })
        })
    ).json();
    return instructions
}

async function main(req: any, res: any) {
    const { inputMint, outputMint, amount, slippageBps } = req.body
    const connection = new Connection(clusterApiUrl('devnet'));
    const swapIx = await getSwap({
        inputMint: inputMint as string,
        outputMint: outputMint as string,
        slippageBps: slippageBps as number,
        amount: amount as number
    })
    const blockhash = (await connection.getLatestBlockhash()).blockhash;
    const {
        tokenLedgerInstruction, // If you are using `useTokenLedger = true`.
        computeBudgetInstructions, // The necessary instructions to setup the compute budget.
        setupInstructions, // Setup missing ATA for the users.
        swapInstruction: swapInstructionPayload, // The actual swap instruction.
        cleanupInstruction, // Unwrap the SOL if `wrapAndUnwrapSol = true`.
        addressLookupTableAddresses, // The lookup table addresses that you can use if you are using versioned transaction.
    } = swapIx;

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

    const addressLookupTableAccounts: AddressLookupTableAccount[] = [];
    addressLookupTableAccounts.push(
        ...(await getAddressLookupTableAccounts(addressLookupTableAddresses))
    );

    let ixs = [
        ...setupInstructions.map(deserializeInstruction),
        ...computeBudgetInstructions.map(deserializeInstruction),
        deserializeInstruction(swapInstructionPayload),
        deserializeInstruction(cleanupInstruction),
    ]

    let txMsg = new TransactionMessage({
        payerKey: keypair.publicKey,
        instructions: ixs,
        recentBlockhash: blockhash
    })


    let txResponse = await rpc.vaultTransactionCreate({
        connection: connection,
        feePayer: keypair,
        multisigPda: multisigAddress,
        transactionIndex: 1n,
        creator: keypair.publicKey,
        vaultIndex: 0,
        ephemeralSigners: 0,
        transactionMessage: txMsg,
        addressLookupTableAccounts: addressLookupTableAccounts,
    })

    console.log(txResponse)
}

main({
    body: {
        inputMint: "So11111111111111111111111111111111111111112",
        outputMint: "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        amount: 100000,
        slippageBps: 1,
    }
}, {})