package gov.nist.spectrumbrowser.client;

import java.util.logging.Logger;

import com.google.gwt.core.client.Scheduler;
import com.google.gwt.maps.client.MapWidget;
import com.google.gwt.maps.client.base.LatLngBounds;

class SelectBySys2DetectCommand implements Scheduler.ScheduledCommand {
	private static Logger logger = Logger.getLogger("SpectrumBrowser");
	private String sys2Detect;
	private MapWidget map;
	private SpectrumBrowserShowDatasets spectrumBrowserShowDatasets;

	public SelectBySys2DetectCommand(String system2detect, 
			SpectrumBrowserShowDatasets spectrumBrowserShowDatasets) {
		this.sys2Detect = system2detect;
		this.spectrumBrowserShowDatasets = spectrumBrowserShowDatasets;
		this.map = spectrumBrowserShowDatasets.getMap();
	}

	@Override
	public void execute() {
		
		int counter = 0;
		LatLngBounds bounds = null;
		for (SensorInformation marker : spectrumBrowserShowDatasets.getSensorMarkers()) {
			if (sys2Detect == null || marker.containsSys2Detect(sys2Detect)) {
				counter ++;
				marker.setVisible(true);
				if (bounds == null) {
					bounds = LatLngBounds.newInstance(marker.getLatLng(), marker.getLatLng());
				}
				bounds.extend(marker.getLatLng());
			} else {
				marker.setVisible(false);
			}
		}
		if ( counter != 0) {
			map.fitBounds(bounds);
		}
	}

}