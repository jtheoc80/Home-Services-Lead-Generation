import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

async function runIngestionScript(scriptName: string) {
  try {
    const { stdout, stderr } = await execAsync(`tsx ${scriptName}`, {
      cwd: '/home/runner/workspace/scripts',
      timeout: 60000
    });
    if (stdout) console.log(stdout);
    if (stderr) console.error(stderr);
  } catch (error: any) {
    console.error(`Error running ${scriptName}:`, error.message);
  }
}

async function runScheduledIngestion() {
  console.log(`\n🕐 Starting scheduled ingestion at ${new Date().toISOString()}`);
  console.log(`⏰ Next run in 6 hours\n`);
  
  await runIngestionScript('ingest_houston.ts');
  await runIngestionScript('ingest_austin.ts');
  
  console.log(`\n✅ Scheduled ingestion cycle complete\n`);
}

async function runContinuously() {
  await runScheduledIngestion();
  
  while (true) {
    await new Promise(resolve => setTimeout(resolve, 6 * 60 * 60 * 1000));
    await runScheduledIngestion();
  }
}

runContinuously();
