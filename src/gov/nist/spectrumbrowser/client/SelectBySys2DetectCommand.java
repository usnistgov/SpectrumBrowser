package gov.nist.spectrumbrowser.client;

import java.util.logging.Logger;

import com.google.gwt.core.client.GWT;
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
		this.map = SpectrumBrowserShowDatasets.getMap();
	}

	@Override
	public void execute() {
		
		
		int counter = 0;
		LatLngBounds bounds = null;
		for (SensorInfoDisplay marker : spectrumBrowserShowDatasets.getSensorMarkers()) {
			if (sys2Detect == null || marker.containsSys2Detect(sys2Detect)) {
				counter ++;
				if (bounds == null) {
					bounds = LatLngBounds.newInstance(marker.getLatLng(), marker.getLatLng());
				}
				bounds.extend(marker.getLatLng());
			} 
		}
		if ( counter != 0) {
			map.fitBounds(bounds);
		}
		SensorGroupMarker.clearAllSelected();
		SensorGroupMarker.showMarkers();
	}

}