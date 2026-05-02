GUIDE = """
╔══════════════════════════════╗
║   📖 ব্যবহার বিধি / User Guide  ║
╚══════════════════════════════╝

এই বটে আপনি নিজের Crypto Wallet ব্যবহার করে সরাসরি যেকাউকে USDC/USDT পাঠাতে পারবেন।

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔐 SETUP (প্রথমবার সেটআপ)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

১. /setup কমান্ড দিন
২. আপনার Network বেছে নিন
   • Solana → USDC
   • Polygon → USDC
   • BSC → USDT (BEP20)
   • Avalanche → USDT
   • Ethereum → USDT/USDC
   • Base → USDC
   • Tron → USDT (TRC20)
   • TON → TON

৩. আপনার Private Key দিন
   ⚠️ Private Key কখনো কাউকে দেবেন না
   ⚠️ Bot কখনো raw key store করে না
   ✅ AES-256 encryption দিয়ে নিরাপদ রাখা হয়

৪. একটি Password তৈরি করুন
   • এই password দিয়ে আপনার key encrypt হবে
   • Password ভুললে key recover করা যাবে না
   • শক্তিশালী password ব্যবহার করুন

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 BALANCE দেখা
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/mybalance → আপনার wallet এর balance দেখুন (Password লাগবে)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💸 SEND করা
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/send_wallet → নিজের wallet থেকে পাঠান

ধাপ:
১. /send_wallet দিন
২. Destination wallet address দিন
৩. পরিমাণ দিন
৪. Password দিন
৫. Confirm করুন → পাঠানো হবে!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔑 KEY পরিবর্তন / মুছে ফেলা
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/changekey → নতুন wallet setup করুন
/deletekey → আপনার key মুছে ফেলুন

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ গুরুত্বপূর্ণ সতর্কতা
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔴 Private Key কখনো কাউকে দেবেন না
🔴 Password ভুলে গেলে key recover হবে না
🔴 Transaction irreversible — পাঠানোর আগে যাচাই করুন
🔴 Gas fee এর জন্য native token রাখুন
   • Solana → SOL
   • BSC → BNB
   • Polygon → MATIC
   • Ethereum → ETH
   • Tron → TRX (Energy)
   • Base → ETH
   • Avalanche → AVAX
   • TON → TON

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📞 সমস্যায় যোগাযোগ করুন
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@MdMouno
"""

NETWORK_GUIDE = {
    "solana": """
🔵 Solana Network Guide:
• Token: USDC
• Private Key format: Base58 (88 characters)
• Example: 4B3fosvyUYMZ73hj...
• Wallet: Phantom, Solflare
• Speed: ~1 second
• Fee: ~$0.001
""",
    "bsc": """
🟡 BSC (BEP20) Network Guide:
• Token: USDT
• Private Key format: Hex (64 characters, without 0x)
• Example: a1b2c3d4e5f6...
• Wallet: MetaMask, Trust Wallet
• Speed: ~3 seconds
• Fee: ~$0.10
""",
    "polygon": """
🟣 Polygon Network Guide:
• Token: USDC
• Private Key format: Hex (64 characters, without 0x)
• Example: a1b2c3d4e5f6...
• Wallet: MetaMask
• Speed: ~2 seconds
• Fee: ~$0.01
""",
    "trc20": """
🔴 Tron (TRC20) Network Guide:
• Token: USDT
• Private Key format: Hex (64 characters)
• Example: a1b2c3d4e5f6...
• Wallet: TronLink, Klever
• Speed: ~3 seconds
• Fee: TRX Energy/Bandwidth
""",
    "ethereum": """
🔷 Ethereum (ERC20) Network Guide:
• Token: USDT
• Private Key format: Hex (64 characters, without 0x)
• Example: a1b2c3d4e5f6...
• Wallet: MetaMask
• Speed: ~15 seconds
• Fee: ~$5-20 (gas price অনুযায়ী)
""",
    "ethereum_usdc": """
🔷 Ethereum USDC Network Guide:
• Token: USDC
• Private Key format: Hex (64 characters, without 0x)
• Wallet: MetaMask
• Fee: ETH gas required
""",
    "base": """
🔵 Base Network Guide:
• Token: USDC
• Private Key format: Hex (64 characters, without 0x)
• Example: a1b2c3d4e5f6...
• Wallet: MetaMask, Coinbase Wallet
• Speed: ~2 seconds
• Fee: ~$0.01
""",
    "avalanche": """
🔺 Avalanche Network Guide:
• Token: USDT
• Private Key format: Hex (64 characters, without 0x)
• Example: a1b2c3d4e5f6...
• Wallet: MetaMask, Core Wallet
• Speed: ~2 seconds
• Fee: ~$0.05
""",
    "ton": """
🔵 TON Network Guide:
• Token: TON
• Wallet address format: UQ... or EQ...
• Wallet: Tonkeeper, MyTonWallet
• Fee: TON
""",
}
