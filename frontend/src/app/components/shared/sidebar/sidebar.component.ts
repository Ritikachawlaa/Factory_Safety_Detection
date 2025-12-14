import { Component } from '@angular/core';
import { Router } from '@angular/router';

interface NavModule {
  id: string;
  label: string;
  icon: string;
  route: string;
  color: string;
}

@Component({
  selector: 'app-sidebar',
  templateUrl: './sidebar.component.html',
  styleUrls: ['./sidebar.component.css']
})
export class SidebarComponent {
  modules: NavModule[] = [
    {
      id: 'human',
      label: 'Human Detection',
      icon: '👤',
      route: '/dashboard/human',
      color: 'blue'
    },
    {
      id: 'vehicle',
      label: 'Vehicle Detection',
      icon: '🚗',
      route: '/dashboard/vehicle',
      color: 'green'
    },
    {
      id: 'helmet',
      label: 'Helmet / PPE Detection',
      icon: '⛑️',
      route: '/dashboard/helmet',
      color: 'yellow'
    },
    {
      id: 'loitering',
      label: 'Loitering Detection',
      icon: '⏱️',
      route: '/dashboard/loitering',
      color: 'orange'
    },
    {
      id: 'labour-count',
      label: 'People / Labour Count',
      icon: '👥',
      route: '/dashboard/labour-count',
      color: 'purple'
    },
    {
      id: 'crowd',
      label: 'Crowd Density',
      icon: '🏢',
      route: '/dashboard/crowd',
      color: 'red'
    },
    {
      id: 'box-count',
      label: 'Box Production Counting',
      icon: '📦',
      route: '/dashboard/box-count',
      color: 'indigo'
    },
    {
      id: 'line-crossing',
      label: 'Line Crossing',
      icon: '➡️',
      route: '/dashboard/line-crossing',
      color: 'pink'
    },
    {
      id: 'tracking',
      label: 'Auto Tracking',
      icon: '🎯',
      route: '/dashboard/tracking',
      color: 'teal'
    },
    {
      id: 'motion',
      label: 'Smart Motion Detection',
      icon: '💨',
      route: '/dashboard/motion',
      color: 'cyan'
    },
    {
      id: 'face-detection',
      label: 'Face Detection',
      icon: '😊',
      route: '/dashboard/face-detection',
      color: 'lime'
    },
    {
      id: 'face-recognition',
      label: 'Face Recognition',
      icon: '🔍',
      route: '/dashboard/face-recognition',
      color: 'amber'
    }
  ];

  constructor(public router: Router) {}

  isActive(route: string): boolean {
    return this.router.url === route || this.router.url.startsWith(route);
  }
}
