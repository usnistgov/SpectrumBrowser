/*
* Conditions Of Use 
* 
* This software was developed by employees of the National Institute of
* Standards and Technology (NIST), and others. 
* This software has been contributed to the public domain. 
* Pursuant to title 15 Untied States Code Section 105, works of NIST
* employees are not subject to copyright protection in the United States
* and are considered to be in the public domain. 
* As a result, a formal license is not needed to use this software.
* 
* This software is provided "AS IS."  
* NIST MAKES NO WARRANTY OF ANY KIND, EXPRESS, IMPLIED
* OR STATUTORY, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
* MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT
* AND DATA ACCURACY.  NIST does not warrant or make any representations
* regarding the use of the software or the results thereof, including but
* not limited to the correctness, accuracy, reliability or usefulness of
* this software.
*/
package gov.nist.spectrumbrowser.client;

import java.util.logging.Logger;

import com.google.gwt.core.client.GWT;
import com.google.gwt.core.client.Scheduler;
import com.google.gwt.maps.client.MapWidget;
import com.google.gwt.maps.client.base.LatLngBounds;
import com.google.gwt.user.client.Timer;

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
		for (SensorInfoDisplay marker : spectrumBrowserShowDatasets
				.getSensorMarkers()) {
			if (sys2Detect == null || marker.containsSys2Detect(sys2Detect)) {
				counter++;
				if (bounds == null) {
					bounds = LatLngBounds.newInstance(marker.getLatLng(),
							marker.getLatLng());
				}
				bounds.extend(marker.getLatLng());
			}
		}

		
		if (counter != 0) {
			SpectrumBrowserShowDatasets.clearSelectedSensor();
			SensorGroupMarker.clearAllSelected();
			map.fitBounds(bounds);
			SensorGroupMarker.showMarkers();
			spectrumBrowserShowDatasets.showHelp();
		}

	}

}