import express from "express";
import {
    Connection,
    ComputeBudgetProgram,
    Keypair,
    PublicKey,
    TransactionMessage,
    AddressLookupTableAccount,
    TransactionInstruction,
    VersionedTransaction,
} from '@solana/web3.js';
import bs58 from "bs58";
import fetch from "cross-fetch";
import {Wallet} from "@project-serum/anchor";
import * as multisig from "@sqds/multisig";
import { Express } from "express-serve-static-core";

let rpc = "https://api.mainnet-beta.solana.com";
const rpcEnv = process.env.RPC
if (rpcEnv !== undefined) {
    rpc = rpcEnv.trim()
}
else {
    console.log(`The "RPC" environment variable was not set. Using the default, public, RPC: ${rpc}`);
}
const pkeyEnv = process.env.SOLANA_PRIVATE_KEY
if (pkeyEnv === undefined) {
    throw new Error("Environment variable `SOLANA_PRIVATE_KEY` not set.");
}
const pkey = pkeyEnv.trim()
const keypair = Keypair.fromSecretKey(bs58.decode(pkey));
const feePayer = new Wallet(keypair).payer;

const port = 3000;
const app = express();
app.use(express.json())

// number of ephemeral signing PDAs required by the transaction
const base64 = "base64";
const ephemeralSigners = 0;
const vaultIndex = 0;
const internalServerErrorCode = 500;
const multisigAddressEnv = process.env.MULTISIG_ADDRESS
if (multisigAddressEnv === undefined) {
    throw new Error("Environment variable `MULTISIG_ADDRESS` not set.");
}
const multisigAddress = new PublicKey(multisigAddressEnv);
const vaultEnv = process.env.VAULT_ADDRESS
if (vaultEnv === undefined) {
    throw new Error("Environment variable `VAULT_ADDRESS` not set.");
}
const squadVault = new PublicKey(vaultEnv);

/**
 * Get the multisig's index for the next transaction.
 */
const getTransactionIndex = async (
    connection: any,
) => {
    const multisigAccount = await multisig.accounts.Multisig.fromAccountAddress(
        connection,
        multisigAddress,
    );
    return multisig.utils.toBigInt(multisigAccount.transactionIndex) + 1n;
}

/**
 * Send transactions with retry.
 */

const sendTx = async (
    connection: any,
    instructions: any,
    resendAmount: number,
    lookupTableAccounts: any = [],
) => {
    const blockhash = await connection.getLatestBlockhash();
    const messageV0 = new TransactionMessage({
        payerKey: feePayer.publicKey,
        recentBlockhash: blockhash.blockhash,
        instructions,
    }).compileToV0Message(lookupTableAccounts);
    const tx = new VersionedTransaction(messageV0);
    tx.sign([feePayer, ...[]]);
    let txSignature: any;
    for (let i = 0; i < resendAmount; i++) {
        try {
            txSignature = await connection.sendTransaction(tx);
        } catch (err) {
            console.log(err);
        }
    }
    return txSignature;
}

/**
 * Send and confirm transactions with retry.
 */
const sendTxAndConfirm = async(
    connection: any,
    instructions: any,
    resendAmount: number,
    lookupTableAccounts: any = [],
    commitment: any = 'finalized',
) => {
    const txSignature = await sendTx(connection, instructions, resendAmount, lookupTableAccounts);
    await connection.confirmTransaction(txSignature, commitment);
    return txSignature;
};

app.post('/tx', async (req: any, res: any) => {
    try {
        let {inputMint, outputMint, amount, slippageBps, priorityFee, timeoutInMs, computeUnitLimit, maxRetries, resendAmount} = req.body
        if (timeoutInMs === undefined) {
            timeoutInMs = 60_000
        }
        if (maxRetries === undefined) {
            maxRetries = 5;
        }
        if (computeUnitLimit === undefined) {
            computeUnitLimit = 1_000_000;
        }
        if (resendAmount === undefined) {
            resendAmount = 100;
        }
        const config = {
            confirmTransactionInitialTimeout: timeoutInMs,
        };
        const connection = new Connection(rpc, config);

        // get a quote from the Jupiter API, required to construct the instructions for the swap
        const url = `https://quote-api.jup.ag/v6/quote?inputMint=${inputMint}&outputMint=${outputMint}&amount=${amount}&slippageBps=${slippageBps}&onlyDirectRoutes=true&maxAccounts=10`;
        const quoteResponse = await (
            await fetch(url)
        ).json();
        // get the instructions for the swap from the Jupiter API, using the retrieved quote
        const instructions = await (
            await fetch('https://quote-api.jup.ag/v6/swap-instructions', {
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
            addressLookupTableAddresses, // The lookup table addresses to be used for versioned transactions.
        } = instructions;

        /**
         Deserialize the instructions returned from the Jupiter API into the format expected by the squads SDK
         */
        const deserializeInstruction = (instruction: any) => {
            return new TransactionInstruction({
                programId: new PublicKey(instruction.programId),
                keys: instruction.accounts.map((key: any) => ({
                    pubkey: new PublicKey(key.pubkey),
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

        // get the address lookup table accounts
        const addressLookupTableAccounts: AddressLookupTableAccount[] = [];
        addressLookupTableAccounts.push(
            ...(await getAddressLookupTableAccounts(addressLookupTableAddresses))
        );
        // create an instruction to set the priority fee
        const priorityFeeInstruction = ComputeBudgetProgram.setComputeUnitPrice({microLamports: priorityFee});
        // create the swap instructions for a squads transaction, using the instructions returned by the Jupiter API
        const swapInstructions = [
            ...setupInstructions.map(deserializeInstruction),
            deserializeInstruction(swapInstructionPayload),
            deserializeInstruction(cleanupInstruction)
        ]
        // get the latest block's hash
        const blockhash = await connection.getLatestBlockhash()
        // create a swap tx message - no need to compile it to v0, this is done by `vaultTransactionCreate` below
        const swapMessage = new TransactionMessage({
            payerKey: squadVault,
            recentBlockhash: blockhash.blockhash,
            instructions: swapInstructions,
        });
        // get the multisig's PDA
        const multisigPda = multisigAddress;
        // get the transaction's index
        let transactionIndex = await getTransactionIndex(connection)
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

        // TX #1 Create the multisig transaction
        await sendTxAndConfirm(connection, [priorityFeeInstruction, createInstructions], resendAmount);
        console.log("Created squad transaction.")

        // propose the transaction for approval/rejection
         const proposalInstructions = multisig.instructions.proposalCreate({
            creator: feePayer.publicKey,
            multisigPda,
            transactionIndex,
        });

        // TX #2 Create the proposal for the multisig tx
        await sendTxAndConfirm(connection, [proposalInstructions], resendAmount);
        console.log("Created proposal for the transaction.")

        // approve the proposal
        const approvalInstructions = multisig.instructions.proposalApprove({
            member: feePayer.publicKey,
            multisigPda,
            transactionIndex,
        });
        
        // TX #3 Approve the proposal (multisig transaction)
        await sendTxAndConfirm(connection, [approvalInstructions], resendAmount);
        console.log("Approved proposal.")

        // execute the transaction
        const {instruction, lookupTableAccounts} = await multisig.instructions.vaultTransactionExecute({
            connection,
            member: feePayer.publicKey,
            multisigPda,
            transactionIndex,
        });
        const computeLimitInstruction = ComputeBudgetProgram.setComputeUnitLimit({
            units: computeUnitLimit,
        })
        
        // TX #4 Execute the multisig transaction
        const txSignature = await sendTxAndConfirm(connection, [computeLimitInstruction, instruction], resendAmount, lookupTableAccounts);
        console.log("Transaction executed.")

        res.json({"status": "ok", "txId": txSignature, "url": `https://solscan.io/tx/${txSignature}`})
    } catch (e: any) {
        console.log(e)
        res.status(internalServerErrorCode).json({"status": "error", "message": e.message})
    }

});

app.use(express.json());
app.listen(port, () => {
    console.log(`Server is running on http://localhost:${port}`);
});
function async(arg0: Express) {
    throw new Error("Function not implemented.");
}

