const fs = require('fs');
const express = require('express');
const bs58 = require('bs58');
const fetch = require('cross-fetch');
const { Wallet } = require('@project-serum/anchor');
const { Connection, Keypair, Transaction, clusterApiUrl } = require('@solana/web3.js');

const rpc = clusterApiUrl('devnet');
const key = fs.readFileSync('./solana_private_key.txt', 'utf-8').trim()
const keypair = Keypair.fromSecretKey(bs58.decode(key));
const wallet = new Wallet(keypair);

const port = 3000;
const app = express();

app.post('/tx', async (req, res) => {
    const { inputMint, outputMint, amount, slippageBps } = req.body
    const connection = new Connection(rpc, 'confirmed');

    const quoteResponse = await (
        await fetch(`https://quote-api.jup.ag/v6/quote
            ?inputMint=${inputMint}\
            &outputMint=${outputMint}\
            &amount=${amount}\
            &slippageBps=${slippageBps}`
        )
    ).json();

    const { swapTransaction } = await (
        await fetch('https://quote-api.jup.ag/v6/swap', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                quoteResponse,
                userPublicKey: wallet.publicKey.toString(),
                wrapAndUnwrapSol: true,
            })
        })
    ).json();

    const swapTransactionBuf = Buffer.from(swapTransaction, 'base64');
    var transaction = VersionedTransaction.deserialize(swapTransactionBuf);
    transaction.sign([wallet.payer]);

    // Execute the transaction
    const rawTransaction = transaction.serialize()
    const txid = await connection.sendRawTransaction(rawTransaction, {
        skipPreflight: true,
        maxRetries: 2
    });
    await connection.confirmTransaction(txid);
    console.log(`https://solscan.io/tx/${txid}`);
});

app.use(express.json());
app.listen(port, () => {
    console.log(`Server is running on http://localhost:${port}`);
});
