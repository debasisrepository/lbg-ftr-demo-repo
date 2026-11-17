import type { OwnerView } from '../../types/api';

interface OwnerBlockProps {
  owner: OwnerView;
}

export function OwnerBlock({ owner }: OwnerBlockProps) {
  return (
    <div>
      <dt className="text-gray-600 text-sm">Owner</dt>
      <dd className="text-sm">{owner.owner_display_name}</dd>
    </div>
  );
}
