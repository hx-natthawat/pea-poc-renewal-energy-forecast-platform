"use client";

import {
  Activity,
  BarChart3,
  Battery,
  CheckCircle2,
  ChevronRight,
  Clock,
  Gauge,
  Globe,
  LineChart,
  Network,
  PlayCircle,
  Server,
  Sun,
  TrendingUp,
  XCircle,
  Zap,
} from "lucide-react";
import { HelpTrigger } from "@/components/help";

interface TORFunctionProps {
  number: number;
  torRef: string;
  helpSectionId: string;
  titleTh: string;
  titleEn: string;
  description: string;
  status: "implemented" | "simulation" | "not_implemented";
  pocTests?: string[];
  accuracy?: string;
  endpoints?: string[];
  icon: React.ReactNode;
  onClick?: () => void;
}

function TORFunctionCard({
  number,
  torRef,
  helpSectionId,
  titleTh,
  titleEn,
  description,
  status,
  pocTests,
  accuracy,
  endpoints,
  icon,
  onClick,
}: TORFunctionProps) {
  const statusConfig = {
    implemented: {
      bg: "bg-green-50 border-green-200",
      badge: "bg-green-100 text-green-800",
      icon: <CheckCircle2 className="w-5 h-5 text-green-600" />,
      label: "Implemented",
      labelTh: "พร้อมใช้งาน",
    },
    simulation: {
      bg: "bg-amber-50 border-amber-200",
      badge: "bg-amber-100 text-amber-800",
      icon: <Clock className="w-5 h-5 text-amber-600" />,
      label: "Simulation",
      labelTh: "จำลอง",
    },
    not_implemented: {
      bg: "bg-gray-50 border-gray-200",
      badge: "bg-gray-100 text-gray-600",
      icon: <XCircle className="w-5 h-5 text-gray-400" />,
      label: "Not Implemented",
      labelTh: "ยังไม่พัฒนา",
    },
  };

  const config = statusConfig[status];

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (onClick && (e.key === "Enter" || e.key === " ")) {
      e.preventDefault();
      onClick();
    }
  };

  const interactiveProps = onClick
    ? {
        onClick,
        onKeyDown: handleKeyDown,
        role: "button" as const,
        tabIndex: 0,
      }
    : {};

  return (
    <div
      className={`rounded-xl border-2 ${config.bg} p-4 sm:p-5 transition-all hover:shadow-lg ${
        onClick ? "cursor-pointer hover:scale-[1.02]" : ""
      }`}
      {...interactiveProps}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-white rounded-lg shadow-sm">{icon}</div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-pea-purple bg-pea-purple/10 px-2 py-0.5 rounded">
                F{number}
              </span>
              <HelpTrigger
                sectionId={helpSectionId}
                size="sm"
                variant="subtle"
                label={`View ${torRef} details`}
              />
            </div>
            <h3 className="font-semibold text-gray-900 text-sm sm:text-base mt-1">{titleEn}</h3>
            <p className="text-xs text-gray-500">{titleTh}</p>
          </div>
        </div>
        {onClick && <ChevronRight className="w-5 h-5 text-gray-400" />}
      </div>

      {/* Status Badge */}
      <div className="flex items-center gap-2 mb-3">
        {config.icon}
        <span className={`text-xs font-medium px-2 py-1 rounded-full ${config.badge}`}>
          {config.label} / {config.labelTh}
        </span>
      </div>

      {/* Description */}
      <p className="text-sm text-gray-600 mb-3">{description}</p>

      {/* POC Tests */}
      {pocTests && pocTests.length > 0 && (
        <div className="mb-3">
          <p className="text-xs font-medium text-gray-500 mb-1">POC Tests:</p>
          <div className="flex flex-wrap gap-1">
            {pocTests.map((test) => (
              <span
                key={test}
                className="text-xs bg-pea-purple/10 text-pea-purple px-2 py-0.5 rounded"
              >
                {test}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Accuracy Target */}
      {accuracy && (
        <div className="flex items-center gap-2 mb-3">
          <TrendingUp className="w-4 h-4 text-green-600" />
          <span className="text-xs text-gray-600">
            Target: <span className="font-medium text-green-700">{accuracy}</span>
          </span>
        </div>
      )}

      {/* API Endpoints */}
      {endpoints && endpoints.length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          <p className="text-xs font-medium text-gray-500 mb-1">API Endpoints:</p>
          <div className="space-y-1">
            {endpoints.map((endpoint) => (
              <code
                key={endpoint}
                className="block text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded font-mono"
              >
                {endpoint}
              </code>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

interface TORPortalProps {
  onNavigate?: (tab: string) => void;
}

export function TORPortal({ onNavigate }: TORPortalProps) {
  const functions: TORFunctionProps[] = [
    {
      number: 1,
      torRef: "TOR 7.5.1.2",
      helpSectionId: "tor-7.5.1.2",
      titleTh: "พยากรณ์กำลังผลิตไฟฟ้าจากพลังงานหมุนเวียน",
      titleEn: "RE Forecast",
      description:
        "Predict renewable energy power output (Solar PV, Wind, Biomass) using weather data and ML models. Supports Intraday and Day-Ahead horizons.",
      status: "implemented",
      pocTests: ["POC 1: Intraday", "POC 2: Day-Ahead"],
      accuracy: "MAPE < 10%",
      endpoints: ["POST /api/v1/forecast/solar", "GET /api/v1/dayahead/solar"],
      icon: <Sun className="w-6 h-6 text-amber-500" />,
      onClick: () => onNavigate?.("solar"),
    },
    {
      number: 2,
      torRef: "TOR 7.5.1.2",
      helpSectionId: "tor-actual-demand",
      titleTh: "พยากรณ์ความต้องการใช้ไฟฟ้าจริงตามจุดซื้อขาย",
      titleEn: "Actual Demand Forecast",
      description:
        "Forecast net demand at trading points. Formula: Actual Demand = Gross Load - BTM RE + Battery flow. Supports prosumer net metering.",
      status: "simulation",
      accuracy: "MAPE < 5%",
      endpoints: ["POST /api/v1/demand-forecast/predict", "GET /api/v1/demand-forecast/predict"],
      icon: <BarChart3 className="w-6 h-6 text-blue-500" />,
      onClick: () => onNavigate?.("grid"),
    },
    {
      number: 3,
      torRef: "TOR 7.5.1.3",
      helpSectionId: "tor-7.5.1.3",
      titleTh: "พยากรณ์ความต้องการใช้ไฟฟ้าระดับพื้นที่",
      titleEn: "Load Forecast",
      description:
        "Multi-level load forecasting: System (MAPE<3%), Regional (5%), Provincial (8%), Substation (8%), Feeder (12%). Covers 12 PEA regions.",
      status: "simulation",
      accuracy: "MAPE < 3-12% by level",
      endpoints: ["POST /api/v1/load-forecast/predict", "GET /api/v1/load-forecast/predict"],
      icon: <LineChart className="w-6 h-6 text-purple-500" />,
      onClick: () => onNavigate?.("grid"),
    },
    {
      number: 4,
      torRef: "TOR 7.5.1.4",
      helpSectionId: "tor-7.5.1.4",
      titleTh: "พยากรณ์ค่าความไม่สมดุลของการซื้อขายไฟฟ้า",
      titleEn: "Imbalance Forecast",
      description:
        "Predict system imbalance for grid stability. Formula: Imbalance = Demand - Scheduled Gen - RE Gen. Includes reserve recommendations.",
      status: "simulation",
      accuracy: "MAE < 5% of avg load",
      endpoints: [
        "POST /api/v1/imbalance-forecast/predict",
        "GET /api/v1/imbalance-forecast/status/{area}",
      ],
      icon: <Gauge className="w-6 h-6 text-orange-500" />,
      onClick: () => onNavigate?.("grid"),
    },
    {
      number: 5,
      torRef: "TOR 7.5.1.5",
      helpSectionId: "tor-7.5.1.5",
      titleTh: "พยากรณ์แรงดันไฟฟ้าในระบบจำหน่ายทุกระดับแรงดัน",
      titleEn: "Voltage Prediction",
      description:
        "Predict voltage levels across LV/MV distribution networks. Monitors prosumer connections, detects overvoltage/undervoltage before occurrence.",
      status: "implemented",
      pocTests: ["POC 3: Intraday", "POC 4: Day-Ahead"],
      accuracy: "MAE < 2V (LV)",
      endpoints: ["POST /api/v1/forecast/voltage", "GET /api/v1/dayahead/voltage"],
      icon: <Zap className="w-6 h-6 text-yellow-500" />,
      onClick: () => onNavigate?.("voltage"),
    },
    {
      number: 6,
      torRef: "TOR 7.5.1.6",
      helpSectionId: "tor-7.5.1.6",
      titleTh: "พยากรณ์กรอบการทำงานแบบพลวัตของแหล่งผลิตไฟฟ้า",
      titleEn: "Dynamic Operating Envelope (DOE)",
      description:
        "Calculate dynamic export/import limits for DER at each connection point. Replaces static limits with time-varying constraints based on network conditions.",
      status: "not_implemented",
      accuracy: "Violation Rate < 1%",
      endpoints: [],
      icon: <Battery className="w-6 h-6 text-gray-400" />,
    },
    {
      number: 7,
      torRef: "TOR 7.5.1.7",
      helpSectionId: "tor-7.5.1.7",
      titleTh: "พยากรณ์ขีดความสามารถในการรองรับการเชื่อมต่อระบบ",
      titleEn: "Hosting Capacity Forecast",
      description:
        "Forecast maximum DER capacity that can connect to each network point. Supports planning decisions and identifies upgrade needs.",
      status: "not_implemented",
      accuracy: "± 10%",
      endpoints: [],
      icon: <Network className="w-6 h-6 text-gray-400" />,
    },
  ];

  const implementedCount = functions.filter((f) => f.status === "implemented").length;
  const simulationCount = functions.filter((f) => f.status === "simulation").length;
  const notImplementedCount = functions.filter((f) => f.status === "not_implemented").length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-pea-purple to-pea-purple-muted rounded-xl p-5 sm:p-6 text-white">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-white/20 rounded-lg">
            <Globe className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl sm:text-2xl font-bold">TOR 7 Functions Portal</h1>
            <p className="text-pea-gold-light text-sm">แพลตฟอร์มศูนย์ข้อมูลพยากรณ์พลังงานหมุนเวียน กฟภ.</p>
          </div>
        </div>

        {/* Status Summary */}
        <div className="grid grid-cols-3 gap-3 sm:gap-4">
          <div className="bg-white/10 rounded-lg p-3 text-center">
            <div className="flex items-center justify-center gap-2 mb-1">
              <CheckCircle2 className="w-5 h-5 text-green-300" />
              <span className="text-2xl font-bold">{implementedCount}</span>
            </div>
            <p className="text-xs text-white/80">Implemented</p>
          </div>
          <div className="bg-white/10 rounded-lg p-3 text-center">
            <div className="flex items-center justify-center gap-2 mb-1">
              <Clock className="w-5 h-5 text-amber-300" />
              <span className="text-2xl font-bold">{simulationCount}</span>
            </div>
            <p className="text-xs text-white/80">Simulation</p>
          </div>
          <div className="bg-white/10 rounded-lg p-3 text-center">
            <div className="flex items-center justify-center gap-2 mb-1">
              <XCircle className="w-5 h-5 text-gray-300" />
              <span className="text-2xl font-bold">{notImplementedCount}</span>
            </div>
            <p className="text-xs text-white/80">Pending</p>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mt-4">
          <div className="flex justify-between text-xs mb-1">
            <span>Implementation Progress</span>
            <span>{Math.round(((implementedCount + simulationCount) / 7) * 100)}%</span>
          </div>
          <div className="h-2 bg-white/20 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-green-400 to-pea-gold-light rounded-full transition-all"
              style={{ width: `${((implementedCount + simulationCount) / 7) * 100}%` }}
            />
          </div>
        </div>
      </div>

      {/* POC Scope Indicator */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <PlayCircle className="w-5 h-5 text-blue-600 mt-0.5" />
          <div>
            <h3 className="font-semibold text-blue-900">POC Scope</h3>
            <p className="text-sm text-blue-700 mt-1">
              POC 1-4 covers <strong>Function 1 (RE Forecast)</strong> and{" "}
              <strong>Function 5 (Voltage Prediction)</strong> with both Intraday and Day-Ahead
              horizons using Data Set 1 (Solar) and Data Set 2-3 (Voltage).
            </p>
          </div>
        </div>
      </div>

      {/* Functions Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {functions.map((func) => (
          <TORFunctionCard key={func.number} {...func} />
        ))}
      </div>

      {/* Infrastructure Info */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <Server className="w-5 h-5 text-gray-600 mt-0.5" />
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-gray-900">Infrastructure</h3>
              <HelpTrigger
                sectionId="tor-7.1"
                size="sm"
                variant="subtle"
                label="View TOR 7.1 details"
              />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-3 text-sm">
              <div>
                <p className="text-gray-500">Web Server</p>
                <p className="font-medium">4 Core, 6GB RAM</p>
              </div>
              <div>
                <p className="text-gray-500">AI/ML Server</p>
                <p className="font-medium">16 Core, 64GB RAM</p>
              </div>
              <div>
                <p className="text-gray-500">Database Server</p>
                <p className="font-medium">8 Core, 32GB RAM</p>
              </div>
            </div>
            <div className="flex flex-wrap gap-2 mt-3">
              <span className="text-xs bg-gray-200 px-2 py-1 rounded">TimescaleDB</span>
              <span className="text-xs bg-gray-200 px-2 py-1 rounded">Redis</span>
              <span className="text-xs bg-gray-200 px-2 py-1 rounded">Kubernetes</span>
              <span className="text-xs bg-gray-200 px-2 py-1 rounded">Helm</span>
              <span className="text-xs bg-gray-200 px-2 py-1 rounded">ArgoCD</span>
              <span className="text-xs bg-gray-200 px-2 py-1 rounded">Kong API Gateway</span>
            </div>
          </div>
        </div>
      </div>

      {/* Compliance Info */}
      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <Activity className="w-5 h-5 text-green-600 mt-0.5" />
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-green-900">TOR Compliance Status</h3>
              <HelpTrigger
                sectionId="tor-overview"
                size="sm"
                variant="subtle"
                label="View TOR overview"
              />
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-3 text-sm">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-green-600" />
                <span>CI/CD</span>
                <HelpTrigger
                  sectionId="tor-7.1.4"
                  size="sm"
                  variant="subtle"
                  label="View TOR 7.1.4 details"
                />
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-green-600" />
                <span>Licensing</span>
                <HelpTrigger
                  sectionId="tor-7.1.5"
                  size="sm"
                  variant="subtle"
                  label="View TOR 7.1.5 details"
                />
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-green-600" />
                <span>Audit Log</span>
                <HelpTrigger
                  sectionId="tor-7.1.6"
                  size="sm"
                  variant="subtle"
                  label="View TOR 7.1.6 details"
                />
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-green-600" />
                <span>Scalability</span>
                <HelpTrigger
                  sectionId="tor-7.1.7"
                  size="sm"
                  variant="subtle"
                  label="View TOR 7.1.7 details"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
