import { formatDateTime } from '../../lib/utils';
import type { ExpectedByView } from '../../types/api';

interface ExpectedByBlockProps {
  expectedBy: ExpectedByView;
}

export function ExpectedByBlock({ expectedBy }: ExpectedByBlockProps) {
  return (
    <div>
      <dt className="text-gray-600 text-sm">Expected by</dt>
      <dd className="text-sm">
        {expectedBy.expected_by_at 
          ? formatDateTime(expectedBy.expected_by_at)
          : 'Timing is under review'}
      </dd>
    </div>
  );
}
