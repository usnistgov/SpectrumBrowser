package gov.nist.spectrumbrowser.client;

import com.google.gwt.core.client.Scheduler;
import com.google.gwt.maps.client.MapWidget;
import com.google.gwt.maps.client.base.LatLngBounds;

class SelectFreqCommand implements Scheduler.ScheduledCommand {
	private FrequencyRange freqRange;
	private MapWidget map;
	private SpectrumBrowserShowDatasets spectrumBrowserShowDatasets;

	public SelectFreqCommand(String system2detect, long minFreq,
			long maxFreq, SpectrumBrowserShowDatasets spectrumBrowserShowDatasets) {
		this.freqRange = new FrequencyRange(system2detect, minFreq, maxFreq);
		this.map = spectrumBrowserShowDatasets.getMap();
		this.spectrumBrowserShowDatasets = spectrumBrowserShowDatasets;
		
	}

	@Override
	public void execute() {
		int counter = 0;		
		LatLngBounds bounds = null;
		for (SensorInformation marker : spectrumBrowserShowDatasets.getSensorMarkers()) {
			// 0 and 0 indicates no freq selection has been done.
			if (freqRange.minFreq == 0 && freqRange.maxFreq == 0) {
				if (bounds == null ) {
					bounds = LatLngBounds.newInstance(marker.getLatLng(), marker.getLatLng());
				}
				marker.setVisible(true);
				bounds.extend(marker.getLatLng());
				counter ++;
			} else if (marker.getFrequencyRanges().contains(this.freqRange)) {
				marker.setVisible(true);
				if (bounds == null) {
					bounds = LatLngBounds.newInstance(marker.getLatLng(), marker.getLatLng());
				}
				bounds.extend(marker.getLatLng());
				counter++;
			} else {
				marker.setVisible(false);
			}
		}
		if ( counter != 0) {
			map.fitBounds(bounds);
		}
		
	}

}