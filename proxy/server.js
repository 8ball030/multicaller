const express = require('express');
const { Connection, Transaction, clusterApiUrl, SystemProgram, PublicKey } = require('@solana/web3.js');

const rpc = clusterApiUrl('devnet');
const key = fs.readFileSync('./solana_private_key.txt', 'utf-8')

const port = 3000;
const app = express();

app.post('/tx', async (req, res) => {
    const { instructions, recent_blockhash } = req.body;
    const connection = new Connection(rpc, 'confirmed');
    const walletKeyPair = new Transaction().add({
        keys: [{ pubkey: new PublicKey(key), isSigner: true, isWritable: true }],
        programId: SystemProgram.programId,
        data: Buffer.alloc(0),
    });

    const transaction = new Transaction().add(instructions);
    transaction.recentBlockhash = recent_blockhash;
    transaction.sign(walletKeyPair);

    const signature = await connection.sendTransaction(transaction, [walletKeyPair]);
    res.json({ signature });
});

app.use(express.json());
app.listen(port, () => {
    console.log(`Server is running on http://localhost:${port}`);
});



