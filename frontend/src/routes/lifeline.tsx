import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Button, InlineNotification } from '@carbon/react';
import { ArrowLeft } from '@carbon/icons-react';
import { apiClient } from '../lib/api-client';
import {
  getLifelineCache,
  setLifelineCache,
  getCacheAgeSeconds,
  formatCacheAge,
  type LifelineCache,
} from '../lib/lifeline-cache';
import { LifelineGuidanceList } from '../components/status/LifelineGuidanceList';
import { CacheAgeNote } from '../components/status/CacheAgeNote';
import styles from './lifeline.module.css';

/**
 * Lifeline page - guidance and fallback options during disruptions
 * Public route (no authentication required)
 */
export function LifelinePage() {
  const [data, setData] = useState<LifelineCache | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isFromCache, setIsFromCache] = useState(false);
  
  const loadLifeline = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await apiClient.get<LifelineCache>('/lifeline');
      setData(response);
      setIsFromCache(false);
      
      // Save to cache for offline use
      setLifelineCache(response);
    } catch (err) {
      // Fall back to cached data
      const cached = getLifelineCache();
      if (cached) {
        setData(cached);
        setIsFromCache(true);
      } else {
        setError('Could not load lifeline guidance. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };
  
  useEffect(() => {
    loadLifeline();
  }, []);
  
  if (loading && !data) {
    return (
      <div className={`cds--stack-scale-6 ${styles.container}`}>
        <p>Loading guidance...</p>
      </div>
    );
  }
  
  if (error && !data) {
    return (
      <div className={`cds--stack-scale-6 ${styles.container}`}>
        <InlineNotification
          kind="error"
          title="Could not load guidance"
          subtitle={error}
          hideCloseButton
        />
        <Button onClick={loadLifeline}>Try again</Button>
      </div>
    );
  }
  
  if (!data) {
    return null;
  }
  
  const cacheAge = isFromCache ? getCacheAgeSeconds(data) : 0;
  const cacheAgeText = formatCacheAge(cacheAge);
  
  // Find phone option for main "Talk to a person" button
  const phoneOption = data.fallback_channels.find(
    (ch) => ch.channel_type === 'phone'
  );
  
  return (
    <div className={`cds--stack-scale-6 ${styles.container}`}>
      <Link to="/status" className={styles.backLink}>
        <ArrowLeft size={16} />
        Service status
      </Link>
      
      <header className="cds--stack-scale-3">
        <h1 className="cds--productive-heading-05">What you can do now</h1>
        <p className={styles.description}>
          Guidance for the current problem. It stays available even if the rest of the app is slow.
        </p>
      </header>
      
      {isFromCache && (
        <CacheAgeNote ageText={cacheAgeText} onRetry={loadLifeline} />
      )}
      
      <LifelineGuidanceList
        items={data.guidance_items}
        category="what_still_works"
        title="What still works"
      />
      
      <LifelineGuidanceList
        items={data.guidance_items}
        category="what_is_affected"
        title="What is affected"
      />
      
      <LifelineGuidanceList
        items={data.guidance_items}
        category="protective_action"
        title="Protect yourself"
      />
      
      <section className="cds--stack-scale-3" aria-labelledby="contact-h">
        <h2 className="cds--productive-heading-02" id="contact-h">
          Ways to reach us
        </h2>
        <div className="cds--stack-scale-3">
          {data.fallback_channels.map((channel) => (
            <div key={channel.channel_type} className={styles.channelOption}>
              <div>
                <p className={`cds--productive-heading-01 ${styles.channelTitle}`}>
                  {channel.label}
                </p>
                {channel.availability_text && (
                  <p className={`cds--label-01 ${styles.channelMeta}`}>
                    {channel.availability_text}
                  </p>
                )}
              </div>
              {channel.contact_detail && channel.channel_type === 'phone' && (
                <a
                  href={`tel:${channel.contact_detail}`}
                  className="cds--btn cds--btn--ghost cds--btn--sm"
                >
                  Call
                </a>
              )}
            </div>
          ))}
        </div>
      </section>
      
      {phoneOption && (
        <Button
          as="a"
          href={`tel:${phoneOption.contact_detail}`}
          kind="primary"
          className={styles.talkButton}
        >
          Talk to a person
        </Button>
      )}
      
      <hr className={styles.divider} />
      
      <section className="cds--stack-scale-5" aria-labelledby="live-h">
        {!isFromCache && (
          <>
            <div>
              <span className={styles.stateLabel}>
                When live guidance can be reached
              </span>
              <h2 className="cds--productive-heading-02" id="live-h">
                Up to date
              </h2>
            </div>
            <InlineNotification
              kind="info"
              lowContrast
              hideCloseButton
              title=""
              subtitle="This guidance was updated recently and is saved on your phone for next time. If it is withdrawn, we replace it the next time your phone connects."
            />
          </>
        )}
      </section>
    </div>
  );
}
