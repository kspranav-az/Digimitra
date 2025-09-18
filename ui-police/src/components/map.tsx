'use client';

import { useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet-defaulticon-compatibility/dist/leaflet-defaulticon-compatibility.css';
import "leaflet-defaulticon-compatibility";
import { mockCameras } from '@/lib/mock-data';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import Image from 'next/image';
import { Button } from '@/components/ui/button';
import { LatLngTuple } from 'leaflet';

// Define a type that matches the mock data structure and includes optional properties
interface Camera {
  id: string;
  name: string;
  status: string;
  position: LatLngTuple; // Use the specific LatLngTuple type from Leaflet
  thumbnailUrl?: string; // This property is optional
}

const Map = () => {
  const [selectedCamera, setSelectedCamera] = useState<Camera | null>(null);

  const MapEvents = () => {
    useMapEvents({
      click() {
        // You can add logic here if needed when the map is clicked
      },
    });
    return null;
  };

  const handleMarkerClick = (camera: Camera) => {
    setSelectedCamera(camera);
  };

  return (
    <>
      <MapContainer center={[34.0522, -118.2437]} zoom={13} style={{ height: '100%', width: '100%' }}>
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
        />
        {/* By casting mockCameras, we inform TypeScript about the data's shape */}
        {(mockCameras as Camera[]).map((camera) => (
          <Marker key={camera.id} position={camera.position}>
            <Popup>
              <b>{camera.name}</b><br />
              Status: {camera.status}<br />
              <Button size="sm" className="mt-2" onClick={() => handleMarkerClick(camera)}>Live Feed</Button>
            </Popup>
          </Marker>
        ))}
        <MapEvents />
      </MapContainer>

      <Dialog open={selectedCamera !== null} onOpenChange={() => setSelectedCamera(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{selectedCamera?.name} - Live Feed</DialogTitle>
          </DialogHeader>
          <div>
            <Image src={selectedCamera?.thumbnailUrl ?? ''} alt={selectedCamera?.name ?? 'Live feed'} width={400} height={300} className="rounded-md" />
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default Map;
