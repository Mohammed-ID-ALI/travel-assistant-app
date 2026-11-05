const express = require('express');
const cors = require('cors');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 5000;

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, '../frontend')));

const db = {
  trips: [
    {
      id: 'trip_guilin',
      destination: 'Guilin & Yangshuo',
      country: 'China',
      start_date: '2026-11-05',
      end_date: '2026-11-09',
      budget: 1200,
      currency: 'USD',
      style: 'Nature & Karst Landscapes',
      weather_summary: '21°C · Crisp Autumn Breeze',
      notes: 'Li River bamboo raft cruise and Yangshuo countryside cycling.',
      itinerary: [
        { id: 'i1', day: 1, time: '09:00', title: 'Elephant Trunk Hill & Two Rivers Walk', category: 'Sightseeing', location: 'Guilin Center', cost: 15, completed: true },
        { id: 'i2', day: 1, time: '12:30', title: 'Authentic Guilin Rice Noodles Lunch', category: 'Dining', location: 'Zhengyang Pedestrian Street', cost: 8, completed: true },
        { id: 'i3', day: 2, time: '08:30', title: 'Li River Scenic Cruise to Yangshuo', category: 'Transport', location: 'Mopanshan Pier', cost: 65, completed: false }
      ],
      expenses: [
        { id: 'e1', title: 'High-Speed Rail Tickets', category: 'Transport', amount: 95, date: '2026-11-05' },
        { id: 'e2', title: 'Riverside Boutique Hotel (4 Nights)', category: 'Lodging', amount: 340, date: '2026-11-05' }
      ],
      packing: [
        { id: 'p1', item: 'Passport & Train E-Ticket', category: 'Documents', packed: true },
        { id: 'p2', item: 'Lightweight Windbreaker', category: 'Clothing', packed: true },
        { id: 'p3', item: 'Portable Power Bank (20,000mAh)', category: 'Electronics', packed: false }
      ]
    }
  ]
};

app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', service: 'WanderFlow Express Backend', timestamp: new Date().toISOString() });
});

app.get('/api/trips', (req, res) => {
  res.json({ trips: db.trips });
});

app.post('/api/trips', (req, res) => {
  const trip = {
    id: req.body.id || `trip_${Date.now()}`,
    destination: req.body.destination,
    country: req.body.country || 'International',
    start_date: req.body.start_date,
    end_date: req.body.end_date,
    budget: Number(req.body.budget || 1500),
    currency: req.body.currency || 'USD',
    style: req.body.style || 'Cultural & Scenic',
    weather_summary: req.body.weather_summary || '22°C · Pleasant',
    notes: req.body.notes || '',
    itinerary: [],
    expenses: [],
    packing: []
  };
  db.trips.push(trip);
  res.status(201).json({ status: 'created', trip });
});

app.delete('/api/trips/:tripId', (req, res) => {
  db.trips = db.trips.filter(t => t.id !== req.params.tripId);
  res.json({ status: 'deleted', id: req.params.tripId });
});

app.post('/api/trips/:tripId/itinerary', (req, res) => {
  const trip = db.trips.find(t => t.id === req.params.tripId);
  if (!trip) return res.status(404).json({ error: 'Trip not found' });
  const item = {
    id: req.body.id || `itin_${Date.now()}`,
    day: Number(req.body.day || 1),
    time: req.body.time || '09:00',
    title: req.body.title,
    category: req.body.category || 'Sightseeing',
    location: req.body.location || 'City Center',
    cost: Number(req.body.cost || 0),
    completed: Boolean(req.body.completed)
  };
  trip.itinerary.push(item);
  res.status(201).json({ status: 'created', item });
});

app.post('/api/trips/:tripId/expenses', (req, res) => {
  const trip = db.trips.find(t => t.id === req.params.tripId);
  if (!trip) return res.status(404).json({ error: 'Trip not found' });
  const expense = {
    id: req.body.id || `exp_${Date.now()}`,
    title: req.body.title,
    category: req.body.category || 'Dining',
    amount: Number(req.body.amount || 0),
    date: req.body.date || new Date().toISOString().slice(0, 10)
  };
  trip.expenses.push(expense);
  res.status(201).json({ status: 'created', expense });
});

app.post('/api/assistant/ask', (req, res) => {
  const { destination = 'your destination', budget = 1500, spent = 0 } = req.body;
  const remaining = Math.max(0, Number(budget) - Number(spent));
  res.json({
    reply: `For ${destination} (Remaining budget: $${remaining.toFixed(0)}): Combine morning landmarks by district, reserve popular dining spots early, and use local transit passes.`,
    suggested_activity: {
      day: 1,
      time: '16:30',
      title: `Sunset Panorama & Cultural Walk (${destination})`,
      category: 'Sightseeing',
      location: `${destination} Old Quarter`,
      cost: 20
    }
  });
});

app.listen(PORT, () => {
  console.log(`WanderFlow Express Server listening at http://localhost:${PORT}`);
});
