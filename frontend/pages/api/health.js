export default async function handler(req, res) {
  // Health check endpoint for Railway deployment monitoring
  // Returns status and server uptime information
  
  if (req.method === 'GET') {
    return res.status(200).json({
      status: 'ok',
      uptime: process.uptime()
    });
  } else {
    res.setHeader('Allow', ['GET']);
    return res.status(405).json({ error: 'Method not allowed' });
  }
}