GUIDE = """
ব্যবহার বিধি / User Guide
────────────────
এই গাইডটি আপনার personal wallet setup, balance check, crypto send, key management এবং security practice বোঝার জন্য। Bot দিয়ে transaction করার আগে প্রতিটি ধাপ ভালোভাবে পড়ে নিন।

১. Bot দিয়ে কী করা যাবে
────────────────
• নিজের encrypted wallet ব্যবহার করে supported network-এ crypto পাঠানো যাবে।
• Balance দেখা, wallet key change/delete করা এবং transaction status check করা যাবে।
• Buy flow, Telegram Stars, FAQ, Order Status এবং AI Support menu থেকে আলাদা সাহায্য পাওয়া যাবে।

২. Supported network
────────────────
• Solana: USDC
• Polygon: USDC
• BSC: USDT (BEP20)
• Avalanche: USDT
• Ethereum: USDT / USDC (ERC20)
• Base: USDC
• Tron: USDT (TRC20)
• TON: TON

Network select করার সময় receiving wallet একই network-এর কিনা নিশ্চিত করুন। ভুল network বা ভুল wallet-এ পাঠালে transaction ফিরিয়ে আনা যায় না।

৩. প্রথমবার wallet setup
────────────────
১) /setup কমান্ড দিন।
২) আপনার wallet network বেছে নিন।
৩) private key পাঠান। Bot message পাওয়ার পর key encrypt করে রাখে এবং key message delete করার চেষ্টা করে।
৪) শক্তিশালী password তৈরি করুন। এই password দিয়ে encrypted key unlock হবে।
৫) setup complete হলে wallet address দেখাবে। Address ঠিক আছে কিনা মিলিয়ে নিন।

Password ভুলে গেলে bot আপনার key recover করতে পারবে না। প্রয়োজনে /deletekey দিয়ে পুরনো key মুছে নতুন setup করতে হবে।

৪. Balance check
────────────────
• /mybalance কমান্ড দিন।
• Bot password চাইবে।
• সঠিক password দিলে selected wallet-এর balance দেখাবে।

Balance দেখাতে RPC/API delay হতে পারে। Balance কম দেখালে কিছু সময় পরে আবার check করুন।

৫. নিজের wallet থেকে crypto পাঠানো
────────────────
১) /send_wallet কমান্ড দিন।
২) destination wallet address দিন।
৩) amount লিখুন।
৪) password দিন।
৫) summary দেখে confirm করুন।
৬) transaction successful হলে hash/receipt দেখাবে।

Send করার আগে amount, destination wallet এবং network অবশ্যই মিলিয়ে নিন। Blockchain transaction irreversible।

৬. Gas fee / network fee
────────────────
Token পাঠাতে network fee লাগে। Wallet-এ token ছাড়াও native gas token রাখতে হবে।

• Solana: SOL
• Polygon: MATIC
• BSC: BNB
• Avalanche: AVAX
• Ethereum: ETH
• Base: ETH
• Tron: TRX / Energy / Bandwidth
• TON: TON

Gas কম থাকলে token balance থাকলেও send fail করতে পারে।

৭. Key change বা delete
────────────────
• /changekey: পুরনো key মুছে নতুন wallet setup শুরু করে।
• /deletekey: saved encrypted key delete করে।

Key change/delete করার আগে নিশ্চিত হয়ে নিন, কারণ delete করলে bot থেকে পুরনো encrypted key ফেরত পাওয়া যাবে না।

৮. Security rules
────────────────
• private key, seed phrase বা wallet password কাউকে দেবেন না।
• support/admin কখনো private key বা seed phrase চাইবে না।
• public wallet address share করা যায়, কিন্তু private key share করা যাবে না।
• password শক্তিশালী রাখুন এবং আলাদা জায়গায় নিরাপদে সংরক্ষণ করুন।
• suspicious link, fake support account বা screenshot-এ private key থাকলে share করবেন না।

৯. Order, payment এবং support
────────────────
• Buy order check করতে Order Status menu, /order ORD-XXXXXX বা /status TRXID ব্যবহার করুন।
• Payment করার আগে network, wallet, amount এবং bKash number মিলিয়ে নিন।
• bKash/SMS notice delay হলে order pending/manual review-এ থাকতে পারে।
• FAQ button-এ সাধারণ প্রশ্নের উত্তর আছে।
• দ্রুত guidance দরকার হলে AI Support ব্যবহার করুন। Manual help দরকার হলে @MdMouno-তে যোগাযোগ করুন।

১০. Common problem
────────────────
• Wrong password: আবার সঠিক password দিন। ভুলে গেলে key recover হবে না।
• Insufficient gas: native gas token top up করুন।
• Invalid wallet: selected network অনুযায়ী wallet address দিন।
• Send failed: hash না এলে duplicate send করার আগে support/admin-এর সাথে verify করুন।
• Pending order: Order ID/TrxID সংরক্ষণ করুন এবং status check করুন।
"""

NETWORK_GUIDE = {
    "solana": """
Solana network guide
────────────────
• Asset: USDC
• Private key format: Base58, usually 88 characters
• Common wallet: Phantom, Solflare
• Gas token: SOL
• Note: Keep a small SOL balance for network fee.
""",
    "bsc": """
BSC (BEP20) network guide
────────────────
• Asset: USDT
• Private key format: Hex, 64 characters, without 0x
• Common wallet: MetaMask, Trust Wallet
• Gas token: BNB
• Note: Use BEP20 address only.
""",
    "polygon": """
Polygon network guide
────────────────
• Asset: USDC
• Private key format: Hex, 64 characters, without 0x
• Common wallet: MetaMask
• Gas token: MATIC
• Note: Use Polygon network address.
""",
    "trc20": """
Tron (TRC20) network guide
────────────────
• Asset: USDT
• Private key format: Hex, 64 characters
• Common wallet: TronLink, Klever
• Gas resource: TRX / Energy / Bandwidth
• Note: Use TRC20 wallet address.
""",
    "ethereum": """
Ethereum (ERC20) network guide
────────────────
• Asset: USDT
• Private key format: Hex, 64 characters, without 0x
• Common wallet: MetaMask
• Gas token: ETH
• Note: ERC20 fee can change depending on gas price.
""",
    "ethereum_usdc": """
Ethereum USDC network guide
────────────────
• Asset: USDC
• Private key format: Hex, 64 characters, without 0x
• Common wallet: MetaMask
• Gas token: ETH
• Note: Use ERC20 USDC address only.
""",
    "base": """
Base network guide
────────────────
• Asset: USDC
• Private key format: Hex, 64 characters, without 0x
• Common wallet: MetaMask, Coinbase Wallet
• Gas token: ETH on Base
• Note: Use Base network address.
""",
    "avalanche": """
Avalanche network guide
────────────────
• Asset: USDT
• Private key format: Hex, 64 characters, without 0x
• Common wallet: MetaMask, Core Wallet
• Gas token: AVAX
• Note: Use Avalanche C-Chain compatible address.
""",
    "ton": """
TON network guide
────────────────
• Asset: TON
• Wallet format: UQ... or EQ...
• Common wallet: Tonkeeper, MyTonWallet
• Gas token: TON
• Note: Check memo/comment requirements before sending to exchanges.
""",
}
