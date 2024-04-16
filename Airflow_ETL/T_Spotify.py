import pandas as pd
import logging

def load_csv(file_path):
    logging.info("Extract Data...")
    data = pd.read_csv(file_path)
    logging.info("Data Extract Successfully.")
    return data

def transform_csv(df_spotify):
    logging.info('Starting data cleaning and transformations...')

    if 'Unnamed: 0' in df_spotify.columns:
        df_spotify.drop('Unnamed: 0', axis=1, inplace=True)
        logging.info('Removed redundant index column')
    
    df_spotify.drop(df_spotify[df_spotify['track_id'] == '1kR4gIb7nGxHPI3D2ifs59'].index, axis=0, inplace=True)
    logging.info('Removed specific track with known issues')
    
    df_spotify['duration_min'] = df_spotify['duration_ms'] / 60000
    logging.info('Added new feature: track duration in minutes')

    for col in ['danceability', 'energy', 'loudness', 'speechiness', 'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo']:
        median = df_spotify[col].median()
        df_spotify[col].fillna(median, inplace=True)
        logging.info(f'Filled missing values in {col} with median')

    df_spotify.drop(['mode', 'key'], axis=1, inplace=True)
    logging.info('Removed unnecessary columns')
    
    df_spotify.drop_duplicates(inplace=True)
    logging.info('Removed duplicate records')
    return df_spotify

#def save_csv(df, output_file):
#    logging.info("Saving cleaned data...")
#    df.to_csv(output_file, index=False)
#    logging.info("Data saved successfully.")

#def main():
#    file_path = './Datasets/spotify_dataset.csv'
#    transformed_file = './Datasets/transformed_spotify_df.csv'
#    df = load_csv(file_path)
#    transformed_df = transform_csv(df)
#    save_csv(transformed_df, transformed_file)
#    logging.info('Data transformation process completed successfully')

#if __name__ == '__main__':
#    main()