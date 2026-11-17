import { InlineNotification, Button } from '@carbon/react';
import styles from './CacheAgeNote.module.css';

interface CacheAgeNoteProps {
  ageText: string;
  onRetry: () => void;
}

/**
 * Warning notification shown when displaying cached lifeline data
 */
export function CacheAgeNote({ ageText, onRetry }: CacheAgeNoteProps) {
  return (
    <div className={styles.wrapper}>
      <InlineNotification
        kind="warning"
        lowContrast
        hideCloseButton
        title="Showing saved guidance"
        subtitle={`We could not reach the latest update, so this is the last copy we saved on your phone. It is ${ageText}.`}
      />
      <Button kind="tertiary" size="sm" onClick={onRetry} className={styles.retryButton}>
        Try again
      </Button>
    </div>
  );
}
