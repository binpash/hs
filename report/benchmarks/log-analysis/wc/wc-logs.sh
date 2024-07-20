#!/bin/bash

# Process each compressed log file in the input directory
for gz_file in ${INPUT_DIR}/*.gz; do

    # Determine the base name without the .gz extension
    INPUT=$(basename "${gz_file%.gz}")
    output_file="${OUTPUT_DIR}/${INPUT}.log"

    # Decompress and convert the binary log to ASCII log
    echo "Decompressing and converting $gz_file to $output_file"
    gzip -dc "$gz_file" | "$TOOL" "$MAPPING_FILE" > "$output_file"
    
    # Process the ASCII log file with the rest of the commands
    echo "Processing $output_file"

    # Sort by response codes
    echo "Sorting by response codes..."
    cat "$output_file" | cut -d "\"" -f3 | cut -d ' ' -f2 | sort | uniq -c | sort -rn > "${OUTPUT_DIR}/${INPUT}_response_codes.log"

    # Find broken links (404)
    echo "Finding broken links (404)..."
    awk '($9 ~ /404/)' "$output_file" | awk '{print $7}' | sort | uniq -c | sort -rn > "${OUTPUT_DIR}/${INPUT}_404_broken_links.log"

    # For 502 (bad-gateway)
    echo "Finding 502 errors (bad-gateway)..."
    awk '($9 ~ /502/)' "$output_file" | awk '{print $7}' | sort | uniq -c | sort -r > "${OUTPUT_DIR}/${INPUT}_502_errors.log"

    # Who are requesting broken links (or URLs resulting in 502)
    echo "Finding requests for wp-admin/install.php..."
    awk -F\" '($2 ~ "/wp-admin/install.php"){print $1}' "$output_file" | awk '{print $1}' | sort | uniq -c | sort -r > "${OUTPUT_DIR}/${INPUT}_requests_wp_admin.log"

    # 404 for php files - mostly hacking attempts
    echo "Finding 404 errors for PHP files..."
    awk '($9 ~ /404/)' "$output_file" | awk -F\" '($2 ~ "^GET .*\.php")' | awk '{print $7}' | sort | uniq -c | sort -r | head -n 20 > "${OUTPUT_DIR}/${INPUT}_404_php_files.log"

    # Most requested URLs
    echo "Finding most requested URLs..."
    awk -F\" '{print $2}' "$output_file" | awk '{print $2}' | sort | uniq -c | sort -r > "${OUTPUT_DIR}/${INPUT}_most_requested_urls.log"

    # Most requested URLs containing "ref"
    echo "Finding most requested URLs containing 'ref'..."
    awk -F\" '($2 ~ "ref"){print $2}' "$output_file" | awk '{print $2}' | sort | uniq -c | sort -r > "${OUTPUT_DIR}/${INPUT}_most_requested_urls_ref.log"

    echo "Processing of $output_file completed."
done
