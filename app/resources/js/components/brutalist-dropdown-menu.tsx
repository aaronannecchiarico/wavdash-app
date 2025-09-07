import { useState } from 'react';
import { type Upload } from '@/types';
import { Link } from '@inertiajs/react';
import { 
  BarChart3, 
  Scissors, 
  Gauge,
  Pencil, 
  Download,
  Trash2,
  MoreVertical 
} from 'lucide-react';

interface BrutalistDropdownMenuProps {
  upload: Upload;
}

export function BrutalistDropdownMenu({ upload }: BrutalistDropdownMenuProps) {
  const [isOpen, setIsOpen] = useState(false);

  const menuItems = [
    {
      label: 'AUDIO ANALYSIS',
      icon: BarChart3,
      href: `/uploads/${upload.id}/analysis`,
      status: upload.has_analysis ? 'DONE' : upload.is_analysis_in_progress ? 'PROCESSING' : null,
      color: 'bg-chart-1' // neo-green
    },
    {
      label: 'STEM SEPARATION',
      icon: Scissors,
      href: `/uploads/${upload.id}/stems`,
      status: upload.has_stems ? 'DONE' : upload.is_stem_separation_in_progress ? 'PROCESSING' : null,
      color: 'bg-chart-2' // neo-pink
    },
    {
      label: 'TEMPO EFFECTS',
      icon: Gauge,
      href: `/uploads/${upload.id}/tempo`,
      status: upload.has_tempos ? 'DONE' : upload.is_tempo_processing_in_progress ? 'PROCESSING' : null,
      color: 'bg-chart-4' // neo-blue
    },
    {
      label: 'EDIT',
      icon: Pencil,
      href: `/uploads/${upload.id}/edit`,
      color: 'bg-chart-3' // neo-yellow
    },
    {
      label: 'VIEW DETAILS',
      icon: Download,
      href: `/uploads/${upload.id}`,
      color: 'bg-main'
    }
  ];

  return (
    <div className="relative">
      <button
        className="border-2 border-border bg-main text-main-foreground px-3 py-2 font-heading font-black text-xs uppercase hover:bg-main-foreground hover:text-main transition-colors shadow-shadow hover:shadow-none hover:translate-x-1 hover:translate-y-1"
        onClick={(e) => {
          e.stopPropagation();
          setIsOpen(!isOpen);
        }}
      >
        <MoreVertical className="w-4 h-4" />
      </button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div 
            className="fixed inset-0 z-10" 
            onClick={() => setIsOpen(false)}
          />
          
          {/* Menu */}
          <div className="absolute right-0 top-full mt-2 w-64 border-2 border-border bg-background shadow-shadow z-20">
            <div className="bg-border p-2 border-b-2 border-border">
              <h3 className="font-heading font-black text-xs uppercase tracking-widest text-foreground">
                TRACK ACTIONS
              </h3>
            </div>
            
            <div className="p-2 space-y-1">
              {menuItems.map((item) => (
                <Link
                  key={item.label}
                  href={item.href}
                  className="block w-full p-3 border-2 border-border hover:shadow-shadow hover:-translate-x-1 hover:-translate-y-1 transition-all group"
                  onClick={(e) => {
                    e.stopPropagation();
                    setIsOpen(false);
                  }}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className={`p-2 border-2 border-border ${item.color}`}>
                        <item.icon className="w-4 h-4 text-main-foreground" />
                      </div>
                      <span className="font-heading font-black text-xs uppercase tracking-wide text-foreground">
                        {item.label}
                      </span>
                    </div>
                    
                    {item.status && (
                      <div className={`px-2 py-1 border-2 border-border ${
                        item.status === 'DONE' ? 'bg-chart-1' : 
                        item.status === 'PROCESSING' ? 'bg-chart-3' : 'bg-border'
                      }`}>
                        <span className="text-xs font-heading font-black text-main-foreground">
                          {item.status}
                        </span>
                      </div>
                    )}
                  </div>
                </Link>
              ))}
              
              {/* Delete Action - Special styling */}
              <button
                className="block w-full p-3 border-2 border-red-500 bg-red-500 hover:bg-red-600 hover:shadow-shadow hover:-translate-x-1 hover:-translate-y-1 transition-all group"
                onClick={(e) => {
                  e.stopPropagation();
                  // Handle delete action
                  console.log('Delete upload:', upload.id);
                  setIsOpen(false);
                }}
              >
                <div className="flex items-center space-x-3">
                  <div className="p-2 border-2 border-white bg-white">
                    <Trash2 className="w-4 h-4 text-red-500" />
                  </div>
                  <span className="font-heading font-black text-xs uppercase tracking-wide text-white">
                    DELETE
                  </span>
                </div>
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}