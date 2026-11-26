🌊 When disaster hits, information is the first flood.

During a flood, the same incident arrives dozens of times, in Arabic and English, mixed with rumours nobody can confirm. Response rooms drown in noise, and every minute spent sorting it is a minute nobody is rescued.

For the PromptWars x AI Vibeathon, I built AidMesh 🛰️: a crew of AI agents that turns raw, multilingual crisis reports into a verified, prioritised response plan.

⚙️ How it works:
🔹 A LangChain intake step structures every raw report.
🔹 Four CrewAI agents then work in sequence on Groq: a Verifier that merges duplicates and flags rumours, a Triage Lead that ranks incidents P1 to P3 by threat to life, a Dispatcher that names the nearest resource and the first safe action, and a Communicator that writes bilingual public alerts and rumour corrections.
🔹 Each agent calls real tools: a rule-based credibility score, language detection, geocoding with OpenStreetMap, flood weather from Open-Meteo, and a nearest-resource lookup.

📊 In the recorded demo run, six raw reports from a flood night in Alexandria went in. Out came six structured incidents, a trapped family in Manshiya ranked as priority one, and a viral "dam collapse" post labelled as a rumour with a public correction, in about 106 seconds.

🌐 The project also includes an eight-page animated 3D website with agent consoles and a globe, plus a live mode that runs the real crew on a hosted API.

🤝 Honest limits: the recorded replay covers Alexandria only, the resource registry is sample data, and the rumour score is rule-based. Humans keep the final decision. AidMesh assists dispatchers, it does not replace them.

💻 Code: https://github.com/Alouakhalid/aidmesh
🔗 Live site: https://aidmesh-production.up.railway.app/

I'd love to hear your feedback 🙌

#AI #CrewAI #LangChain #Groq #AgenticAI #CrisisResponse #PromptWars #AIVibeathon
