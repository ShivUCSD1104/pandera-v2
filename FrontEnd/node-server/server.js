const express = require('express');
const cors = require('cors');
const axios = require('axios');
const bodyParser = require('body-parser');

const app = express();
const PORT = process.env.port || 3001; // or any port you prefer

app.use(cors());
app.use(bodyParser.json());

app.post('/api/compute', async (req, res) => {
  console.log('Received request:', req.body);
  try {
    const { parameters, graphType } = req.body;
    const response = await axios.post('https://flask.pandera.net/compute', { parameters, graphType });
    // const response = await axios.post('http://127.0.0.1:5001/compute', { parameters, graphType });
    res.json(response.data);
  } catch (error) {
    console.error('Error communicating with Python server:', error);
    res.status(500).send('Internal Server Error');
  }
});


app.listen(PORT, () => {
  console.log(`Node.js server running on http://localhost:${PORT}`);
});