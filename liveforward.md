### 🔄 The `/liveforward` Command: Real-Time Syncing

The `/liveforward` command is designed for continuous, real-time message forwarding. Once configured, it will automatically listen for and instantly send any new messages from a source chat to your destination.

---

### **Prerequisites & Usage** 🚀

* **Userbot Requirement**
    * __Requirement__: This feature requires a Userbot to function. A standard bot cannot be used for this task.
    * __Note__: The Userbot you use for this task must be a member of all the source chats you want to forward from.

* **Initiate the Task**
    * __Command__: `/liveforward`
    * __Description__: Starts the interactive setup process. The bot will first check if you already have an active live forwarding session.

### **Interactive Flow**

* **Step 1: Choose Your Listener**
    * __Description__: The bot will show a list of all your userbots. Select the one you want to use for this live forwarding task.
    * __Note__: If you only have one userbot, the bot will auto-select it for you.

* **Step 2: Select Your Destination**
    * __Description__: The bot displays a list of your destination channels.
    * __Action__: Click the button corresponding to the channel you want new messages forwarded to.

* **Step 3: Define Your Source(s)**
    * __Description__: This is where you specify the chat(s) you want to listen to.
    * **For Free Users**: You can only add a single source chat. The bot will prompt you to forward a message or send a link from the source.
    * **For Premium Users**: You can add multiple source chats. The bot will ask you to forward a message or send a link from the first source. After adding it, you will see a `Done Adding Sources` button. You can continue adding more sources, one by one, up to your plan's limit.

* **Step 4: Activation & Confirmation**
    * __Description__: Once all sources are added (or after the single source is provided for free users), the bot will activate the live forwarding session. It will send a final confirmation message detailing the Userbot being used, the source chat(s), and the destination chat.
    * __Important__: The bot will apply all your configured filters (from the `/settings` panel) to the messages it forwards.

---

### **Task Control** ⚙️

* **Stopping a Session**
    * __Command__: `/stoplive`
    * __Description__: This command immediately stops all of your active live forwarding sessions.

* **Handling Errors**
    * __FloodWait__: The bot's forwarding mechanism includes a built-in retry mechanism to handle `FloodWait` errors gracefully by waiting the specified amount of time before trying again.
    * __Permissions__: If your Userbot does not have access to a source or destination chat, the bot will notify you with an error message and guide you on what to do.