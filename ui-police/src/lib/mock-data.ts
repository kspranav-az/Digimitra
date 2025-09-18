export const mockCameras = [
  { id: 'cam-01', name: 'CAM-01 Entrance', status: 'active', position: [34.0522, -118.2437] },
  { id: 'cam-02', name: 'CAM-02 Lobby', status: 'active', position: [34.0530, -118.2445] },
  { id: 'cam-03', name: 'CAM-03 Plaza', status: 'offline', position: [34.0525, -118.2430] },
  { id: 'cam-04', name: 'CAM-04 Loading Dock', status: 'active', position: [34.0518, -118.2450] },
  { id: 'cam-05', name: 'CAM-05 Parking Lot', status: 'active', position: [34.0540, -118.2460] },
];

export const mockEvents = [
  {
    id: 'evt-001',
    type: 'Suspicious Activity',
    description: 'A person was seen loitering near the restricted area for over 5 minutes.',
    timestamp: '2024-05-20T10:00:00Z',
    cameraName: 'CAM-01 Entrance',
    severity: 'medium',
  },
  {
    id: 'evt-002',
    type: 'Intrusion Alert',
    description: 'An unauthorized individual has entered the main lobby outside of business hours.',
    timestamp: '2024-05-20T09:30:00Z',
    cameraName: 'CAM-02 Lobby',
    severity: 'high',
  },
  {
    id: 'evt-003',
    type: 'Crowd Formation',
    description: 'A large crowd has formed in the plaza. Monitoring for potential escalations.',
    timestamp: '2024-05-20T09:15:00Z',
    cameraName: 'CAM-03 Plaza',
    severity: 'low',
  },
    {
    id: 'evt-004',
    type: 'Vehicle At Loading Dock',
    description: 'A truck has been at the loading dock for over an hour.',
    timestamp: '2024-05-20T09:00:00Z',
    cameraName: 'CAM-04 Loading Dock',
    severity: 'low',
  },
  {
    id: 'evt-005',
    type: 'Person in Red Shirt',
    description: 'A person in a red shirt was seen running through the parking lot.',
    timestamp: '2024-05-20T08:45:00Z',
    cameraName: 'CAM-05 Parking Lot',
    severity: 'medium',
  },
];
