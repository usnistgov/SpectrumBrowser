package gov.nist.spectrumbrowser.client;

import java.util.logging.Logger;

import com.google.gwt.core.client.Scheduler;
import com.google.gwt.maps.client.MapWidget;
import com.google.gwt.maps.client.base.LatLngBounds;
import com.google.gwt.user.client.Timer;

class SelectFreqCommand implements Scheduler.ScheduledCommand {
	private FrequencyRange freqRange;
	private MapWidget map;
	private SpectrumBrowserShowDatasets spectrumBrowserShowDatasets;
	private static Logger logger = Logger.getLogger("SpectrumBrowser");

	public SelectFreqCommand(String system2detect, long minFreq,
			long maxFreq, SpectrumBrowserShowDatasets spectrumBrowserShowDatasets) {
		this.freqRange = new FrequencyRange(system2detect, minFreq, maxFreq);
		this.map = SpectrumBrowserShowDatasets.getMap();
		this.spectrumBrowserShowDatasets = spectrumBrowserShowDatasets;
		logger.finer("SelectFreqCommand: " + freqRange);
		
	}

	@Override
	public void execute() {
		int counter = 0;		
		LatLngBounds bounds = null;
		for (SensorInfoDisplay marker : spectrumBrowserShowDatasets.getSensorMarkers()) {
			// 0 and 0 indicates no freq selection has been done.
			if (freqRange.minFreq == 0 && freqRange.maxFreq == 0) {
				if (bounds == null ) {
					bounds = LatLngBounds.newInstance(marker.getLatLng(), marker.getLatLng());
				}
				bounds.extend(marker.getLatLng());
				counter ++;
			} else if (marker.getFreqRanges().contains(this.freqRange)) {
				if (bounds == null) {
					bounds = LatLngBounds.newInstance(marker.getLatLng(), marker.getLatLng());
				}
				bounds.extend(marker.getLatLng());
				counter++;
			}  
		}
		logger.finer("SelectFreqCommand: 	Found " + counter + " markers");
		if ( counter != 0) {
			SpectrumBrowserShowDatasets.clearSelectedSensor();
			spectrumBrowserShowDatasets.clearSensorInfoPanel();
			SensorGroupMarker.clearAllSelected();
			map.fitBounds(bounds);
			SensorGroupMarker.showMarkers();

		}
		
		
		
		
	}

}