const { processTopics } = require("./processTopics");

async function runDailyTask() {
    console.log("[Daily Task] Starting daily task at", new Date().toISOString());
    try {
        await processTopics();
        console.log("[Daily Task] Daily task completed successfully");
    } catch (error) {
        console.error("[Daily Task] Error encountered:", error);
    }
}

runDailyTask();