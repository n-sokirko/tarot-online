'use client';

interface CardBackProps {
  rotation?: number;
  className?: string;
}

const CORNER_POSITIONS = [
  'top-3 left-3',
  'top-3 right-3',
  'bottom-3 left-3',
  'bottom-3 right-3',
] as const;

const RAY_ANGLES = [0, 45, 90, 135] as const;

export default function CardBack({ rotation = 0, className = '' }: CardBackProps) {
  return (
    <div
      className={`relative flex-shrink-0 ${className}`}
      style={{
        width: '100%',
        aspectRatio: '2 / 3',
        transform: `rotate(${rotation}deg)`,
      }}
    >
      {/* Outer frame */}
      <div
        className="absolute inset-0 rounded-xl overflow-hidden"
        style={{
          background:
            'linear-gradient(135deg, #1e1245 0%, #0b0b1f 50%, #1e1245 100%)',
          border: '2px solid #d4af37',
          boxShadow:
            '0 0 0 1px #1e1245, inset 0 0 0 1px rgba(212,175,55,0.3)',
        }}
      >
        {/* Inner gold border */}
        <div
          className="absolute inset-2 rounded-lg"
          style={{ border: '1px solid rgba(212,175,55,0.5)' }}
        />

        {/* Corner ornaments */}
        {CORNER_POSITIONS.map((pos) => (
          <div
            key={pos}
            className={`absolute ${pos} w-4 h-4 flex items-center justify-center`}
            style={{ color: '#d4af37', fontSize: '0.6rem' }}
          >
            ✦
          </div>
        ))}

        {/* Center medallion */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="relative flex items-center justify-center">
            {/* Radiating rays */}
            {RAY_ANGLES.map((deg) => (
              <div
                key={deg}
                className="absolute inset-0 flex items-center justify-center"
                style={{ transform: `rotate(${deg}deg)` }}
              >
                <div
                  style={{
                    width: '1px',
                    height: '56px',
                    background:
                      'linear-gradient(to bottom, transparent, rgba(212,175,55,0.4), transparent)',
                  }}
                />
              </div>
            ))}

            {/* Circle ring */}
            <div
              className="w-16 h-16 rounded-full flex items-center justify-center"
              style={{
                border: '1px solid rgba(212,175,55,0.6)',
                background:
                  'radial-gradient(circle, rgba(212,175,55,0.1) 0%, transparent 70%)',
              }}
            >
              {/* Center star */}
              <div
                style={{
                  color: '#d4af37',
                  textShadow: '0 0 8px rgba(212,175,55,0.8)',
                  fontSize: '1.25rem',
                }}
              >
                ✦
              </div>
            </div>
          </div>
        </div>

        {/* Subtle diagonal texture */}
        <div
          className="absolute inset-0 rounded-xl opacity-5"
          style={{
            backgroundImage:
              'repeating-linear-gradient(45deg, #d4af37 0px, #d4af37 1px, transparent 1px, transparent 8px)',
          }}
        />
      </div>
    </div>
  );
}
