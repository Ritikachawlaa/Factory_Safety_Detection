/**
 * MODULE GENERATION SCRIPT
 * 
 * This TypeScript defines the configuration for all 12 modules.
 * Use this as reference to generate the remaining components.
 * 
 * Each module follows the same pattern as module-human but with:
 * - Different feature enablement
 * - Different data extraction from DetectionResult
 * - Different history tracking logic
 */

import { EnabledFeatures } from '../../services/unified-detection.service';

export interface ModuleConfig {
  id: string;
  name: string;
  icon: string;
  subtitle: string;
  enabledFeature: keyof EnabledFeatures;
  primaryStat: {
    label: string;
    icon: string;
    getValue: (result: any) => number | string;
  };
  secondaryStat: {
    label: string;
    icon: string;
    getValue: (result: any) => number | string;
  };
  tertiaryStat: {
    label: string;
    icon: string;
    getValue: (result: any) => number | string;
  };
  historyLabel: (result: any) => string;
  historyValue: (result: any) => any;
}

export const MODULE_CONFIGS: ModuleConfig[] = [
  {
    id: 'human',
    name: 'Human Detection',
    icon: '👤',
    subtitle: 'Real-time people counting and tracking',
    enabledFeature: 'human',
    primaryStat: {
      label: 'Current Count',
      icon: '👥',
      getValue: (r) => r?.people_count || 0
    },
    secondaryStat: {
      label: 'Peak Count',
      icon: '📈',
      getValue: () => 0 // Calculated in component
    },
    tertiaryStat: {
      label: 'Average Count',
      icon: '📊',
      getValue: () => 0 // Calculated in component
    },
    historyLabel: (r) => `${r.people_count} people detected`,
    historyValue: (r) => r.people_count
  },
  {
    id: 'vehicle',
    name: 'Vehicle Detection',
    icon: '🚗',
    subtitle: 'Monitor vehicle traffic and count',
    enabledFeature: 'vehicle',
    primaryStat: {
      label: 'Vehicles Detected',
      icon: '🚙',
      getValue: (r) => r?.vehicle_count || 0
    },
    secondaryStat: {
      label: 'Peak Vehicles',
      icon: '📈',
      getValue: () => 0
    },
    tertiaryStat: {
      label: 'Average Traffic',
      icon: '📊',
      getValue: () => 0
    },
    historyLabel: (r) => `${r.vehicle_count} vehicles detected`,
    historyValue: (r) => r.vehicle_count
  },
  {
    id: 'helmet',
    name: 'Helmet / PPE Detection',
    icon: '⛑️',
    subtitle: 'Safety compliance monitoring',
    enabledFeature: 'helmet',
    primaryStat: {
      label: 'Compliance Rate',
      icon: '✅',
      getValue: (r) => `${r?.ppe_compliance_rate || 0}%`
    },
    secondaryStat: {
      label: 'Violations',
      icon: '⚠️',
      getValue: (r) => r?.helmet_violations || 0
    },
    tertiaryStat: {
      label: 'Compliant',
      icon: '✔️',
      getValue: (r) => r?.helmet_compliant || 0
    },
    historyLabel: (r) => `${r.ppe_compliance_rate}% compliant, ${r.helmet_violations} violations`,
    historyValue: (r) => r.ppe_compliance_rate
  },
  {
    id: 'loitering',
    name: 'Loitering Detection',
    icon: '⏱️',
    subtitle: 'Detect unauthorized presence',
    enabledFeature: 'loitering',
    primaryStat: {
      label: 'Loitering Count',
      icon: '👤',
      getValue: (r) => r?.loitering_count || 0
    },
    secondaryStat: {
      label: 'Status',
      icon: '🚨',
      getValue: (r) => r?.loitering_detected ? 'Alert' : 'Clear'
    },
    tertiaryStat: {
      label: 'Groups Detected',
      icon: '👥',
      getValue: (r) => r?.people_groups || 0
    },
    historyLabel: (r) => r.loitering_detected ? `⚠️ Loitering detected (${r.loitering_count})` : 'Area clear',
    historyValue: (r) => r.loitering_count
  },
  {
    id: 'labour-count',
    name: 'People / Labour Count',
    icon: '👥',
    subtitle: 'Workforce monitoring',
    enabledFeature: 'human',
    primaryStat: {
      label: 'Labour Count',
      icon: '👷',
      getValue: (r) => r?.labour_count || 0
    },
    secondaryStat: {
      label: 'Total People',
      icon: '👥',
      getValue: (r) => r?.people_count || 0
    },
    tertiaryStat: {
      label: 'Groups',
      icon: '🏢',
      getValue: (r) => r?.people_groups || 0
    },
    historyLabel: (r) => `${r.labour_count} workers present`,
    historyValue: (r) => r.labour_count
  },
  {
    id: 'crowd',
    name: 'Crowd Density',
    icon: '🏢',
    subtitle: 'Monitor crowd levels',
    enabledFeature: 'crowd',
    primaryStat: {
      label: 'Density Level',
      icon: '📊',
      getValue: (r) => r?.crowd_density || 'Normal'
    },
    secondaryStat: {
      label: 'Status',
      icon: '🚨',
      getValue: (r) => r?.crowd_detected ? 'Crowded' : 'Normal'
    },
    tertiaryStat: {
      label: 'Occupied Area',
      icon: '📏',
      getValue: (r) => `${r?.occupied_area || 0}%`
    },
    historyLabel: (r) => `${r.crowd_density} density, ${r.occupied_area}% occupied`,
    historyValue: (r) => r.occupied_area
  },
  {
    id: 'box-count',
    name: 'Box Production Counting',
    icon: '📦',
    subtitle: 'Track production output',
    enabledFeature: 'box_count',
    primaryStat: {
      label: 'Box Count',
      icon: '📦',
      getValue: (r) => r?.box_count || 0
    },
    secondaryStat: {
      label: 'Peak Production',
      icon: '📈',
      getValue: () => 0
    },
    tertiaryStat: {
      label: 'Average',
      icon: '📊',
      getValue: () => 0
    },
    historyLabel: (r) => `${r.box_count} boxes counted`,
    historyValue: (r) => r.box_count
  },
  {
    id: 'line-crossing',
    name: 'Line Crossing',
    icon: '➡️',
    subtitle: 'Monitor boundary violations',
    enabledFeature: 'line_crossing',
    primaryStat: {
      label: 'Total Crossings',
      icon: '🔢',
      getValue: (r) => r?.total_crossings || 0
    },
    secondaryStat: {
      label: 'Status',
      icon: '🚦',
      getValue: (r) => r?.line_crossed ? 'Crossed' : 'Clear'
    },
    tertiaryStat: {
      label: 'Tracked Objects',
      icon: '🎯',
      getValue: (r) => r?.tracked_objects || 0
    },
    historyLabel: (r) => r.line_crossed ? '⚠️ Line crossed detected' : 'No crossing',
    historyValue: (r) => r.total_crossings
  },
  {
    id: 'tracking',
    name: 'Auto Tracking',
    icon: '🎯',
    subtitle: 'Object tracking system',
    enabledFeature: 'tracking',
    primaryStat: {
      label: 'Tracked Objects',
      icon: '🎯',
      getValue: (r) => r?.tracked_objects || 0
    },
    secondaryStat: {
      label: 'Peak Tracked',
      icon: '📈',
      getValue: () => 0
    },
    tertiaryStat: {
      label: 'Average',
      icon: '📊',
      getValue: () => 0
    },
    historyLabel: (r) => `${r.tracked_objects} objects tracked`,
    historyValue: (r) => r.tracked_objects
  },
  {
    id: 'motion',
    name: 'Smart Motion Detection',
    icon: '💨',
    subtitle: 'AI-validated motion analysis',
    enabledFeature: 'motion',
    primaryStat: {
      label: 'Motion Intensity',
      icon: '📊',
      getValue: (r) => `${r?.motion_intensity || 0}%`
    },
    secondaryStat: {
      label: 'Status',
      icon: '🎬',
      getValue: (r) => r?.motion_detected ? 'Motion' : 'Still'
    },
    tertiaryStat: {
      label: 'AI Validated',
      icon: '🤖',
      getValue: (r) => r?.motion_ai_validated ? 'Yes' : 'No'
    },
    historyLabel: (r) => r.motion_detected ? `💨 Motion: ${r.motion_intensity}%` : 'No motion',
    historyValue: (r) => r.motion_intensity
  },
  {
    id: 'face-detection',
    name: 'Face Detection',
    icon: '😊',
    subtitle: 'Detect faces in real-time',
    enabledFeature: 'face_detection',
    primaryStat: {
      label: 'Faces Detected',
      icon: '😊',
      getValue: (r) => r?.faces_detected || 0
    },
    secondaryStat: {
      label: 'Peak Faces',
      icon: '📈',
      getValue: () => 0
    },
    tertiaryStat: {
      label: 'Average',
      icon: '📊',
      getValue: () => 0
    },
    historyLabel: (r) => `${r.faces_detected} faces detected`,
    historyValue: (r) => r.faces_detected
  },
  {
    id: 'face-recognition',
    name: 'Face Recognition',
    icon: '🔍',
    subtitle: 'Identify known individuals',
    enabledFeature: 'face_recognition',
    primaryStat: {
      label: 'Recognized',
      icon: '✅',
      getValue: (r) => r?.faces_recognized?.length || 0
    },
    secondaryStat: {
      label: 'Total Faces',
      icon: '😊',
      getValue: (r) => r?.faces_detected || 0
    },
    tertiaryStat: {
      label: 'Unknown',
      icon: '❓',
      getValue: (r) => (r?.faces_detected || 0) - (r?.faces_recognized?.length || 0)
    },
    historyLabel: (r) => {
      const recognized = r.faces_recognized?.length || 0;
      return recognized > 0 ? `${recognized} faces recognized` : 'No faces recognized';
    },
    historyValue: (r) => r.faces_recognized?.length || 0
  }
];
