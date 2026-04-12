const { Worker } = require('bullmq');
const IORedis = require('ioredis');
const { MongoClient } = require('mongodb');
const { spawn } = require('child_process');
require('dotenv').config({ path: '../.env' });

const REDIS_HOST = process.env.REDIS_HOST || 'localhost';
const REDIS_PORT = process.env.REDIS_PORT || 6379;
const MONGODB_URI = process.env.MONGODB_URI || 'mongodb://localhost:27017';
const DB_NAME = 'zeroscrapper';

const connection = new IORedis({
  host: REDIS_HOST,
  port: REDIS_PORT,
  maxRetriesPerRequest: null,
});

async function runPythonScraper(query, requirementId) {
  return new Promise((resolve, reject) => {
    console.log(`Executing Python scraper for: ${query} (Req: ${requirementId})`);
    // Use the absolute path to the venv python if possible, or just python3
    const pythonPath = '../venv/bin/python3';
    const scraperPath = '../pipeline_v3.py';
    
    // Pass requirementId as the second argument
    const pyProcess = spawn(pythonPath, [scraperPath, query, requirementId]);
    
    let output = '';
    pyProcess.stdout.on('data', (data) => {
      const logLine = data.toString().trim();
      if (logLine) console.log(logLine);
      output += data.toString();
    });
    
    pyProcess.stderr.on('data', (data) => {
      const logLine = data.toString().trim();
      if (logLine) console.log(logLine);
    });
    
    pyProcess.on('close', (code) => {
      if (code === 0) {
        resolve(output);
      } else {
        reject(new Error(`Scraper exited with code ${code}`));
      }
    });
  });
}

async function startWorker() {
  const client = new MongoClient(MONGODB_URI);
  await client.connect();
  const db = client.db(DB_NAME);
  const requirementCol = db.collection('user_requirement');
  const statusCol = db.collection('requirement_status');

  console.log('BullMQ Worker started, waiting for jobs...');

  const worker = new Worker('requirement-tasks', async (job) => {
    const { requirement_id, query_text } = job.data;
    console.log(`Processing Job ${job.id}: ${query_text}`);

    try {
      // 1. Update status to 'processing'
      await statusCol.updateOne(
        { requirement_id: requirement_id },
        { $set: { status: 'processing', updated_at: new Date().toISOString() } },
        { upsert: true }
      );

      // 2. Run the Scrapers (Python)
      await runPythonScraper(query_text, requirement_id);

      // 3. Update status to 'completed'
      await statusCol.updateOne(
        { requirement_id: requirement_id },
        { $set: { status: 'completed', updated_at: new Date().toISOString() } }
      );
      
      console.log(`Job ${job.id} completed successfully.`);
    } catch (error) {
      console.error(`Job ${job.id} failed: ${error.message}`);
      await statusCol.updateOne(
        { requirement_id: requirement_id },
        { 
          $set: { 
            status: 'failed', 
            last_error: error.message,
            updated_at: new Date().toISOString() 
          } 
        }
      );
      throw error;
    }
  }, { connection });

  worker.on('failed', (job, err) => {
    console.error(`${job.id} has failed with ${err.message}`);
  });
}

startWorker().catch(console.error);
